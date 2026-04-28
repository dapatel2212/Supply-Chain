from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(120))
    role = db.Column(db.String(20), default='exporter')
    fcm_token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def verify_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'phone': self.phone, 'company': self.company, 'role': self.role
        }


class Port(db.Model):
    __tablename__ = 'ports'
    id = db.Column(db.Integer, primary_key=True)
    port_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    port_name = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(80))
    city = db.Column(db.String(80))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    avg_processing_hours = db.Column(db.Float, default=24.0)
    current_congestion_level = db.Column(db.String(20), default='normal')
    timezone = db.Column(db.String(50), default='UTC')

    def to_dict(self):
        return {
            'id': self.id, 'port_code': self.port_code, 'port_name': self.port_name,
            'country': self.country, 'city': self.city, 'latitude': self.latitude,
            'longitude': self.longitude, 'avg_processing_hours': self.avg_processing_hours,
            'current_congestion_level': self.current_congestion_level
        }


class Shipment(db.Model):
    __tablename__ = 'shipments'
    id = db.Column(db.Integer, primary_key=True)
    shipment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    exporter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    importer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    exporter_name = db.Column(db.String(120))
    importer_name = db.Column(db.String(120))
    origin_warehouse_address = db.Column(db.Text)
    origin_warehouse_city = db.Column(db.String(80))
    origin_warehouse_country = db.Column(db.String(80))
    origin_warehouse_lat = db.Column(db.Float)
    origin_warehouse_lng = db.Column(db.Float)
    origin_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'))
    destination_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'))
    final_destination_address = db.Column(db.Text)
    final_destination_city = db.Column(db.String(80))
    final_destination_country = db.Column(db.String(80))
    final_destination_lat = db.Column(db.Float)
    final_destination_lng = db.Column(db.Float)
    cargo_type = db.Column(db.String(80))
    cargo_description = db.Column(db.Text)
    weight_tons = db.Column(db.Float)
    volume_cbm = db.Column(db.Float)
    container_number = db.Column(db.String(50))
    bill_of_lading = db.Column(db.String(100))
    vessel_name = db.Column(db.String(120))
    vessel_imo = db.Column(db.String(20))
    truck_number = db.Column(db.String(50))
    current_status = db.Column(db.String(50), default='registered', index=True)
    current_phase = db.Column(db.String(50), default='warehouse')
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    current_speed = db.Column(db.Float, default=0)
    initial_eta_truck_arrival = db.Column(db.DateTime)
    initial_eta_port_arrival = db.Column(db.DateTime)
    initial_eta_final_delivery = db.Column(db.DateTime)
    current_eta_truck_arrival = db.Column(db.DateTime)
    current_eta_port_arrival = db.Column(db.DateTime)
    current_eta_final_delivery = db.Column(db.DateTime)
    actual_truck_departure = db.Column(db.DateTime)
    actual_port_arrival = db.Column(db.DateTime)
    actual_vessel_departure = db.Column(db.DateTime)
    actual_vessel_arrival = db.Column(db.DateTime)
    actual_final_delivery = db.Column(db.DateTime)
    truck_distance_km = db.Column(db.Float)
    sea_distance_nm = db.Column(db.Float)
    total_delay_hours = db.Column(db.Float, default=0)
    route_optimization_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'shipment_number': self.shipment_number,
            'exporter_name': self.exporter_name, 'importer_name': self.importer_name,
            'origin_warehouse_city': self.origin_warehouse_city,
            'origin_warehouse_country': self.origin_warehouse_country,
            'origin_warehouse_lat': self.origin_warehouse_lat,
            'origin_warehouse_lng': self.origin_warehouse_lng,
            'final_destination_city': self.final_destination_city,
            'final_destination_country': self.final_destination_country,
            'final_destination_lat': self.final_destination_lat,
            'final_destination_lng': self.final_destination_lng,
            'cargo_type': self.cargo_type, 'weight_tons': self.weight_tons,
            'container_number': self.container_number, 'vessel_name': self.vessel_name,
            'current_status': self.current_status, 'current_phase': self.current_phase,
            'current_lat': self.current_lat, 'current_lng': self.current_lng,
            'current_speed': self.current_speed,
            'initial_eta_final_delivery': self.initial_eta_final_delivery.isoformat() if self.initial_eta_final_delivery else None,
            'current_eta_final_delivery': self.current_eta_final_delivery.isoformat() if self.current_eta_final_delivery else None,
            'truck_distance_km': self.truck_distance_km, 'sea_distance_nm': self.sea_distance_nm,
            'total_delay_hours': self.total_delay_hours,
            'route_optimization_count': self.route_optimization_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TrackingEvent(db.Model):
    __tablename__ = 'tracking_events'
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), index=True)
    event_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(30), default='gps_update')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    speed_kmph = db.Column(db.Float)
    heading_degrees = db.Column(db.Float)
    phase = db.Column(db.String(50))
    location_name = db.Column(db.String(200))
    data_source = db.Column(db.String(30), default='simulated')
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id, 'shipment_id': self.shipment_id,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'event_type': self.event_type, 'latitude': self.latitude,
            'longitude': self.longitude, 'speed_kmph': self.speed_kmph,
            'phase': self.phase, 'location_name': self.location_name,
            'data_source': self.data_source, 'notes': self.notes,
        }


class ShipmentDelay(db.Model):
    __tablename__ = 'shipment_delays'
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), index=True)
    delay_type = db.Column(db.String(40))
    delay_hours = db.Column(db.Float)
    delay_severity = db.Column(db.String(20))
    description = db.Column(db.Text)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    location_name = db.Column(db.String(200))
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    reoptimization_triggered = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id, 'shipment_id': self.shipment_id,
            'delay_type': self.delay_type, 'delay_hours': self.delay_hours,
            'delay_severity': self.delay_severity, 'description': self.description,
            'location_name': self.location_name,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'resolved': self.resolved,
        }


class RoutePlan(db.Model):
    __tablename__ = 'route_plans'
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), index=True)
    version = db.Column(db.Integer, default=1)
    is_current = db.Column(db.Boolean, default=True)
    triggered_by = db.Column(db.String(40), default='initial_registration')
    waypoints = db.Column(db.Text)
    truck_route_polyline = db.Column(db.Text)
    eta_truck_arrival = db.Column(db.DateTime)
    eta_port_departure = db.Column(db.DateTime)
    eta_port_arrival = db.Column(db.DateTime)
    eta_final_delivery = db.Column(db.DateTime)
    truck_distance_km = db.Column(db.Float)
    sea_distance_nm = db.Column(db.Float)
    estimated_total_hours = db.Column(db.Float)
    time_saved_vs_previous = db.Column(db.Float, default=0)
    weather_condition = db.Column(db.String(50))
    port_congestion = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id, 'shipment_id': self.shipment_id, 'version': self.version,
            'is_current': self.is_current, 'triggered_by': self.triggered_by,
            'waypoints': json.loads(self.waypoints) if self.waypoints else [],
            'eta_final_delivery': self.eta_final_delivery.isoformat() if self.eta_final_delivery else None,
            'truck_distance_km': self.truck_distance_km, 'sea_distance_nm': self.sea_distance_nm,
            'estimated_total_hours': self.estimated_total_hours,
            'time_saved_vs_previous': self.time_saved_vs_previous,
            'weather_condition': self.weather_condition,
            'port_congestion': self.port_congestion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ShipmentAlert(db.Model):
    __tablename__ = 'shipment_alerts'
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), index=True)
    alert_type = db.Column(db.String(40))
    severity = db.Column(db.String(20), default='info')
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    requires_action = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'shipment_id': self.shipment_id, 'alert_type': self.alert_type,
            'severity': self.severity, 'title': self.title, 'message': self.message,
            'is_read': self.is_read, 'requires_action': self.requires_action,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MLTrainingData(db.Model):
    __tablename__ = 'ml_training_data'
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'))
    origin_port_code = db.Column(db.String(10))
    destination_port_code = db.Column(db.String(10))
    cargo_type = db.Column(db.String(80))
    weight_tons = db.Column(db.Float)
    truck_distance_km = db.Column(db.Float)
    sea_distance_nm = db.Column(db.Float)
    departure_hour = db.Column(db.Integer)
    departure_day_of_week = db.Column(db.Integer)
    departure_month = db.Column(db.Integer)
    weather_condition = db.Column(db.String(50))
    origin_congestion = db.Column(db.String(20))
    destination_congestion = db.Column(db.String(20))
    actual_truck_hours = db.Column(db.Float)
    actual_origin_port_hours = db.Column(db.Float)
    actual_sea_hours = db.Column(db.Float)
    actual_destination_port_hours = db.Column(db.Float)
    actual_total_hours = db.Column(db.Float)
    was_delayed = db.Column(db.Boolean)
    total_delay_hours = db.Column(db.Float)
    delay_reason = db.Column(db.String(50))
    route_optimizations_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
