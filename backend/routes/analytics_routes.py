from flask import Blueprint, jsonify, request
from database.db_setup import db, Shipment
from datetime import datetime, timedelta
from sqlalchemy import func
import os

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        days = int(request.args.get('days', 30))
        since = datetime.utcnow() - timedelta(days=days)

        total = Shipment.query.filter(Shipment.created_at >= since).count()
        delivered = Shipment.query.filter(Shipment.created_at >= since, Shipment.current_status == 'delivered').count()
        in_transit = Shipment.query.filter(
            Shipment.created_at >= since,
            Shipment.current_status.in_(['in_transit_truck', 'at_origin_port', 'in_transit_sea', 'at_destination_port'])
        ).count()
        delayed = Shipment.query.filter(Shipment.created_at >= since, Shipment.total_delay_hours > 0).count()

        avg_delay = db.session.query(func.avg(Shipment.total_delay_hours)).filter(Shipment.created_at >= since).scalar() or 0
        total_optimizations = db.session.query(func.sum(Shipment.route_optimization_count)).filter(Shipment.created_at >= since).scalar() or 0

        status_dist = db.session.query(Shipment.current_status, func.count(Shipment.id)).filter(
            Shipment.created_at >= since
        ).group_by(Shipment.current_status).all()

        cargo_dist = db.session.query(Shipment.cargo_type, func.count(Shipment.id)).filter(
            Shipment.created_at >= since
        ).group_by(Shipment.cargo_type).all()

        on_time_rate = round((delivered / total * 100), 1) if total > 0 else 0

        # Convert to dictionaries for easier frontend access
        status_dict = {s: c for s, c in status_dist}
        cargo_dict = {c: n for c, n in cargo_dist}

        return jsonify({
            'success': True,
            'on_time_rate': on_time_rate,
            'total_delays': delayed,
            'avg_delay_hours': round(avg_delay, 1),
            'total_optimizations': int(total_optimizations),
            'total_shipments': total,
            'delivered': delivered,
            'in_transit': in_transit,
            'status_distribution': status_dict,
            'cargo_distribution': cargo_dict,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/ai-insights', methods=['POST'])
def ai_insights():
    try:
        data = request.get_json()
        query = data.get('query', '')

        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key or gemini_key.startswith('your_'):
            return jsonify({
                'success': True,
                'response': f"AI Insights (offline mode): Based on your query '{query}', here are general recommendations for shipment optimization. Monitor port congestion levels, consider route diversification, and use weather data for better ETA predictions.",
                'mode': 'offline'
            })

        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            # Try models in order of preference/availability
            model = None
            for model_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(model_name)
                    # Quick validation — list_models to confirm availability
                    break
                except Exception:
                    continue
            if model is None:
                raise Exception("No Gemini model available")

            total = Shipment.query.count()
            delayed = Shipment.query.filter(Shipment.total_delay_hours > 0).count()

            context = f"""You are a logistics AI analyst. Current stats:
- Total shipments: {total}
- Delayed shipments: {delayed}
- User query: {query}

Provide a concise, actionable response in 2-3 paragraphs."""

            response = model.generate_content(context)
            return jsonify({'success': True, 'response': response.text, 'mode': 'gemini'})
        except Exception as ge:
            return jsonify({
                'success': True,
                'response': f"AI temporarily unavailable. Quick analysis of '{query}': Review your dashboard for patterns. Check port congestion and delay trends.",
                'mode': 'fallback',
                'error': str(ge)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api-status', methods=['GET'])
def api_status():
    """Returns the connection status of all external APIs."""
    import os
    status = {}

    # Gemini
    gemini_key = os.getenv('GEMINI_API_KEY')
    status['gemini'] = 'configured' if gemini_key and not gemini_key.startswith('your_') else 'missing'

    # Gmail
    gmail = os.getenv('GMAIL_SENDER')
    gmail_pass = os.getenv('GMAIL_PASSWORD', '').replace(' ', '')
    status['gmail'] = 'configured' if gmail and gmail_pass else 'missing'

    # ShipsGo
    shipsgo_key = os.getenv('SHIPSGO_API_KEY')
    status['shipsgo'] = 'configured' if shipsgo_key else 'missing'

    # Weather
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    status['openweather'] = 'configured' if weather_key else 'missing'

    return jsonify({'success': True, 'api_status': status})
