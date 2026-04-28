from database.db_setup import db, Shipment, TrackingEvent, ShipmentDelay
from datetime import datetime, timedelta
import random


class TrackingService:
    def update_position(self, shipment_id):
        try:
            s = Shipment.query.get(shipment_id)
            if not s or s.current_status == 'delivered':
                return None

            # --- Try ShipsGo for real vessel position (sea phase) ---
            real_position = None
            if s.current_phase == 'sea' and s.vessel_name:
                try:
                    from services.shipsgo_service import ShipsGoService
                    svc = ShipsGoService()
                    # Try container first, then vessel IMO if available
                    if s.container_number:
                        info = svc.get_container_info(s.container_number)
                        if info:
                            lat = info.get('lat') or info.get('Lat') or info.get('latitude')
                            lng = info.get('lon') or info.get('Lon') or info.get('longitude')
                            if lat and lng:
                                real_position = {'lat': float(lat), 'lng': float(lng), 'source': 'shipsgo'}
                except Exception as e:
                    pass  # Silently fall through to simulation

            if real_position:
                lat, lng = real_position['lat'], real_position['lng']
                data_source = 'shipsgo'
            elif s.current_lat and s.final_destination_lat:
                # Simulation fallback
                dlat = s.final_destination_lat - s.current_lat
                dlng = s.final_destination_lng - s.current_lng
                step = random.uniform(0.01, 0.03)
                lat = s.current_lat + dlat * step
                lng = s.current_lng + dlng * step
                data_source = 'simulated'
            else:
                return None

            s.current_lat = lat
            s.current_lng = lng
            s.current_speed = random.uniform(15, 45)

            ev = TrackingEvent(
                shipment_id=shipment_id,
                latitude=lat,
                longitude=lng,
                speed_kmph=s.current_speed,
                phase=s.current_phase,
                data_source=data_source,
                event_type='gps_update'
            )
            db.session.add(ev)
            db.session.commit()

            delay_info = self._check_delay(s)
            return {
                'success': True,
                'position': {'lat': lat, 'lng': lng},
                'delay': delay_info,
                'data_source': data_source
            }
        except Exception as e:
            db.session.rollback()
            print(f"Tracking error: {e}")
            return None

    def _check_delay(self, shipment):
        if random.random() < 0.05:
            delay_hours = round(random.uniform(2, 8), 1)
            delay = ShipmentDelay(
                shipment_id=shipment.id,
                delay_type=random.choice(['traffic', 'weather', 'port_congestion']),
                delay_hours=delay_hours,
                delay_severity='moderate' if delay_hours < 6 else 'major',
                description=f"Detected delay of {delay_hours} hours"
            )
            db.session.add(delay)
            shipment.total_delay_hours = (shipment.total_delay_hours or 0) + delay_hours
            db.session.commit()
            return {
                'has_delay': True,
                'delay_hours': delay_hours,
                'trigger_reoptimize': delay_hours > 4
            }
        return {'has_delay': False, 'trigger_reoptimize': False}
