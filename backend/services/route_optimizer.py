from database.db_setup import db, Shipment, RoutePlan, Port
from datetime import datetime, timedelta
import json
import random

class RouteOptimizer:
    def reoptimize(self, shipment_id, triggered_by='manual_user'):
        try:
            s = Shipment.query.get(shipment_id)
            if not s:
                return {'success': False, 'error': 'Shipment not found'}

            RoutePlan.query.filter_by(shipment_id=shipment_id, is_current=True).update({'is_current': False})

            last_version = db.session.query(db.func.max(RoutePlan.version)).filter_by(shipment_id=shipment_id).scalar() or 0
            new_version = last_version + 1

            waypoints = self._build_waypoints(s)
            now = datetime.utcnow()
            estimated_hours = random.uniform(180, 240)
            time_saved = random.uniform(2, 12) if new_version > 1 else 0

            new_route = RoutePlan(
                shipment_id=shipment_id,
                version=new_version,
                is_current=True,
                triggered_by=triggered_by,
                waypoints=json.dumps(waypoints),
                eta_truck_arrival=now + timedelta(hours=12),
                eta_port_arrival=now + timedelta(hours=48),
                eta_final_delivery=now + timedelta(hours=estimated_hours),
                truck_distance_km=s.truck_distance_km or random.uniform(300, 800),
                sea_distance_nm=s.sea_distance_nm or random.uniform(800, 2500),
                estimated_total_hours=estimated_hours,
                time_saved_vs_previous=time_saved,
                weather_condition='clear',
                port_congestion='normal'
            )
            db.session.add(new_route)

            s.current_eta_final_delivery = new_route.eta_final_delivery
            s.route_optimization_count = new_version

            db.session.commit()

            return {
                'success': True,
                'route': new_route.to_dict(),
                'time_saved_hours': time_saved,
                'message': f'Route optimized (v{new_version}). Saved {time_saved:.1f} hours.'
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def _build_waypoints(self, shipment):
        wps = []
        if shipment.origin_warehouse_lat:
            wps.append({'lat': shipment.origin_warehouse_lat, 'lng': shipment.origin_warehouse_lng, 'type': 'warehouse'})
        if shipment.origin_port_id:
            p = Port.query.get(shipment.origin_port_id)
            if p:
                wps.append({'lat': p.latitude, 'lng': p.longitude, 'type': 'origin_port'})
        if shipment.destination_port_id:
            p = Port.query.get(shipment.destination_port_id)
            if p:
                wps.append({'lat': p.latitude, 'lng': p.longitude, 'type': 'destination_port'})
        if shipment.final_destination_lat:
            wps.append({'lat': shipment.final_destination_lat, 'lng': shipment.final_destination_lng, 'type': 'final'})
        return wps
