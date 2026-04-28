from flask import Blueprint, jsonify, request
from database.db_setup import db, Shipment, Port, TrackingEvent, ShipmentDelay, RoutePlan, ShipmentAlert
from datetime import datetime, timedelta
import random
import string
import json

shipment_bp = Blueprint('shipments', __name__, url_prefix='/api')

@shipment_bp.route('/shipments', methods=['GET'])
def get_shipments():
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        query = Shipment.query
        if status:
            query = query.filter_by(current_status=status)
        shipments = query.order_by(Shipment.created_at.desc()).limit(limit).all()
        
        # Add port codes and current_eta for frontend
        shipments_data = []
        for s in shipments:
            data = s.to_dict()
            origin_port = Port.query.get(s.origin_port_id) if s.origin_port_id else None
            dest_port = Port.query.get(s.destination_port_id) if s.destination_port_id else None
            data['origin_port_code'] = origin_port.port_code if origin_port else 'N/A'
            data['destination_port_code'] = dest_port.port_code if dest_port else 'N/A'
            # Add current_eta alias for frontend
            data['current_eta'] = data.get('current_eta_final_delivery')
            shipments_data.append(data)
        
        return jsonify({'success': True, 'count': len(shipments_data), 'shipments': shipments_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>', methods=['GET'])
def get_shipment(shipment_id):
    try:
        s = Shipment.query.get_or_404(shipment_id)
        origin_port = Port.query.get(s.origin_port_id) if s.origin_port_id else None
        dest_port = Port.query.get(s.destination_port_id) if s.destination_port_id else None
        data = s.to_dict()
        data['origin_port'] = origin_port.to_dict() if origin_port else None
        data['destination_port'] = dest_port.to_dict() if dest_port else None
        # Add flattened port codes for frontend map component
        data['origin_port_code'] = origin_port.port_code if origin_port else 'N/A'
        data['destination_port_code'] = dest_port.port_code if dest_port else 'N/A'
        # Add current_eta alias for frontend
        data['current_eta'] = data.get('current_eta_final_delivery')
        return jsonify({'success': True, 'shipment': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments', methods=['POST'])
def register_shipment():
    try:
        data = request.get_json()
        ship_num = f"SHIP-2024-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        s = Shipment(
            shipment_number=ship_num,
            exporter_name=data.get('exporter_name', 'Unknown'),
            importer_name=data.get('importer_name', 'Unknown'),
            origin_warehouse_address=data.get('origin_warehouse_address'),
            origin_warehouse_city=data.get('origin_warehouse_city'),
            origin_warehouse_country=data.get('origin_warehouse_country'),
            origin_warehouse_lat=data.get('origin_warehouse_lat'),
            origin_warehouse_lng=data.get('origin_warehouse_lng'),
            origin_port_id=data.get('origin_port_id'),
            destination_port_id=data.get('destination_port_id'),
            final_destination_address=data.get('final_destination_address'),
            final_destination_city=data.get('final_destination_city'),
            final_destination_country=data.get('final_destination_country'),
            final_destination_lat=data.get('final_destination_lat'),
            final_destination_lng=data.get('final_destination_lng'),
            cargo_type=data.get('cargo_type'),
            cargo_description=data.get('cargo_description'),
            weight_tons=data.get('weight_tons'),
            volume_cbm=data.get('volume_cbm'),
            container_number=data.get('container_number'),
            vessel_name=data.get('vessel_name'),
            current_status='registered',
            current_phase='warehouse',
            initial_eta_truck_arrival=datetime.utcnow() + timedelta(hours=12),
            initial_eta_port_arrival=datetime.utcnow() + timedelta(days=2),
            initial_eta_final_delivery=datetime.utcnow() + timedelta(days=14),
            current_eta_truck_arrival=datetime.utcnow() + timedelta(hours=12),
            current_eta_port_arrival=datetime.utcnow() + timedelta(days=2),
            current_eta_final_delivery=datetime.utcnow() + timedelta(days=14),
        )
        db.session.add(s)
        db.session.commit()
        return jsonify({'success': True, 'shipment': s.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/status', methods=['PATCH'])
def update_status(shipment_id):
    try:
        s = Shipment.query.get_or_404(shipment_id)
        data = request.get_json()
        s.current_status = data.get('status', s.current_status)
        db.session.commit()
        return jsonify({'success': True, 'shipment': s.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/reoptimize', methods=['POST'])
def reoptimize(shipment_id):
    try:
        from services.route_optimizer import RouteOptimizer
        data = request.get_json() or {}
        optimizer = RouteOptimizer()
        result = optimizer.reoptimize(shipment_id, data.get('triggered_by', 'manual_user'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/add-event', methods=['POST'])
def add_event(shipment_id):
    try:
        data = request.get_json()
        ev = TrackingEvent(
            shipment_id=shipment_id,
            event_type=data.get('event_type', 'gps_update'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            speed_kmph=data.get('speed_kmph'),
            phase=data.get('phase'),
            location_name=data.get('location_name'),
            data_source=data.get('data_source', 'manual'),
            notes=data.get('notes'),
        )
        db.session.add(ev)
        s = Shipment.query.get(shipment_id)
        if s and data.get('latitude'):
            s.current_lat = data.get('latitude')
            s.current_lng = data.get('longitude')
            s.current_speed = data.get('speed_kmph', 0)
        db.session.commit()
        return jsonify({'success': True, 'event': ev.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/tracking-events', methods=['GET'])
def get_events(shipment_id):
    try:
        limit = int(request.args.get('limit', 50))
        events = TrackingEvent.query.filter_by(shipment_id=shipment_id).order_by(TrackingEvent.event_timestamp.desc()).limit(limit).all()
        return jsonify({'success': True, 'count': len(events), 'events': [e.to_dict() for e in events]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/delays', methods=['GET'])
def get_delays(shipment_id):
    try:
        delays = ShipmentDelay.query.filter_by(shipment_id=shipment_id).order_by(ShipmentDelay.detected_at.desc()).all()
        return jsonify({'success': True, 'count': len(delays), 'delays': [d.to_dict() for d in delays]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/current-route', methods=['GET'])
def get_current_route(shipment_id):
    try:
        rp = RoutePlan.query.filter_by(shipment_id=shipment_id, is_current=True).first()
        return jsonify({'success': True, 'route': rp.to_dict() if rp else None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/original-route', methods=['GET'])
def get_original_route(shipment_id):
    try:
        rp = RoutePlan.query.filter_by(shipment_id=shipment_id, version=1).first()
        return jsonify({'success': True, 'route': rp.to_dict() if rp else None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/route-history', methods=['GET'])
def get_route_history(shipment_id):
    try:
        plans = RoutePlan.query.filter_by(shipment_id=shipment_id).order_by(RoutePlan.version.asc()).all()
        return jsonify({'success': True, 'count': len(plans), 'routes': [p.to_dict() for p in plans]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/shipments/<int:shipment_id>/alerts', methods=['GET'])
def get_alerts(shipment_id):
    try:
        alerts = ShipmentAlert.query.filter_by(shipment_id=shipment_id).order_by(ShipmentAlert.created_at.desc()).all()
        return jsonify({'success': True, 'count': len(alerts), 'alerts': [a.to_dict() for a in alerts]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shipment_bp.route('/ports', methods=['GET'])
def get_ports():
    try:
        ports = Port.query.all()
        # Return ports with both 'code'/'name' and 'port_code'/'port_name' for compatibility
        ports_data = []
        for p in ports:
            port_dict = p.to_dict()
            # Add compatibility fields for frontend
            port_dict['code'] = p.port_code
            port_dict['name'] = p.port_name
            ports_data.append(port_dict)
        return jsonify({'success': True, 'count': len(ports_data), 'ports': ports_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
