from database.db_setup import db, User, Port, Shipment, TrackingEvent
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import string


def seed_users():
    if User.query.count() > 0:
        return
    users = [
        User(
            name='Raj Kumar', email='raj@exporters.in',
            password_hash=generate_password_hash('password123'),
            phone='+91-9876543210', company='Indian Exports Ltd', role='exporter'
        ),
        User(
            name='Ahmed Al Mansoori', email='ahmed@importers.ae',
            password_hash=generate_password_hash('password123'),
            phone='+971-501234567', company='Dubai Imports LLC', role='importer'
        ),
        User(
            name='Admin User', email='admin@system.com',
            password_hash=generate_password_hash('admin123'),
            phone='+91-9000000000', company='ShipTrack AI', role='admin'
        ),
    ]
    db.session.bulk_save_objects(users)
    db.session.commit()
    print("✅ Seeded 3 users")


def seed_ports():
    if Port.query.count() > 0:
        return
    ports = [
        Port(port_code='INMUN', port_name='Mundra Port', country='India', city='Mundra',
             latitude=22.7397, longitude=69.7016, avg_processing_hours=18),
        Port(port_code='INNSA', port_name='JNPT Mumbai', country='India', city='Mumbai',
             latitude=18.9490, longitude=72.9525, avg_processing_hours=24, current_congestion_level='high'),
        Port(port_code='INMAA', port_name='Chennai Port', country='India', city='Chennai',
             latitude=13.0967, longitude=80.2925, avg_processing_hours=20),
        Port(port_code='AEJEA', port_name='Jebel Ali', country='UAE', city='Dubai',
             latitude=25.0118, longitude=55.0618, avg_processing_hours=16, current_congestion_level='low'),
        Port(port_code='AEDXB', port_name='Port Rashid', country='UAE', city='Dubai',
             latitude=25.2769, longitude=55.2769, avg_processing_hours=18),
        Port(port_code='SGSIN', port_name='Singapore Port', country='Singapore', city='Singapore',
             latitude=1.2655, longitude=103.8240, avg_processing_hours=12, current_congestion_level='low'),
        Port(port_code='CNSHA', port_name='Shanghai Port', country='China', city='Shanghai',
             latitude=31.2304, longitude=121.4737, avg_processing_hours=22, current_congestion_level='high'),
        Port(port_code='NLRTM', port_name='Rotterdam Port', country='Netherlands', city='Rotterdam',
             latitude=51.9244, longitude=4.4777, avg_processing_hours=14),
    ]
    db.session.bulk_save_objects(ports)
    db.session.commit()
    print("✅ Seeded 8 ports")


def seed_shipments():
    if Shipment.query.count() > 0:
        return

    exporter = User.query.filter_by(email='raj@exporters.in').first()
    importer = User.query.filter_by(email='ahmed@importers.ae').first()
    mundra = Port.query.filter_by(port_code='INMUN').first()
    jnpt = Port.query.filter_by(port_code='INNSA').first()
    jebel_ali = Port.query.filter_by(port_code='AEJEA').first()

    cargo_types = ['Rice', 'Textiles', 'Electronics', 'Spices', 'Auto Parts', 'Furniture']
    statuses = ['registered', 'in_transit_truck', 'at_origin_port', 'in_transit_sea', 'at_destination_port', 'delivered']
    phases = ['warehouse', 'land_origin', 'port_origin', 'sea', 'port_destination', 'completed']

    shipments = []
    for i in range(25):
        idx = i % 6
        ship_num = f"SHIP-2024-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        origin_port = random.choice([mundra, jnpt])
        created = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        s = Shipment(
            shipment_number=ship_num,
            exporter_id=exporter.id, importer_id=importer.id,
            exporter_name=exporter.company, importer_name=importer.company,
            origin_warehouse_address=f"{random.randint(100,999)} Industrial Area",
            origin_warehouse_city='Ahmedabad', origin_warehouse_country='India',
            origin_warehouse_lat=23.0225, origin_warehouse_lng=72.5714,
            origin_port_id=origin_port.id,
            destination_port_id=jebel_ali.id,
            final_destination_address=f"{random.randint(100,999)} Business Bay",
            final_destination_city='Dubai', final_destination_country='UAE',
            final_destination_lat=25.1972, final_destination_lng=55.2744,
            cargo_type=random.choice(cargo_types),
            cargo_description=f"Container of {random.choice(cargo_types).lower()}",
            weight_tons=round(random.uniform(10, 50), 2),
            volume_cbm=round(random.uniform(20, 100), 2),
            container_number=f"MSCU{random.randint(1000000, 9999999)}",
            vessel_name=random.choice(['MSC OSCAR', 'EVER GIVEN', 'CMA CGM JACQUES']),
            truck_number=f"GJ-01-AB-{random.randint(1000, 9999)}",
            current_status=statuses[idx],
            current_phase=phases[idx],
            current_lat=origin_port.latitude + random.uniform(-2, 2),
            current_lng=origin_port.longitude + random.uniform(-2, 2),
            current_speed=random.uniform(0, 25),
            initial_eta_truck_arrival=created + timedelta(hours=12),
            initial_eta_port_arrival=created + timedelta(days=2),
            initial_eta_final_delivery=created + timedelta(days=14),
            current_eta_truck_arrival=created + timedelta(hours=12),
            current_eta_port_arrival=created + timedelta(days=2),
            current_eta_final_delivery=created + timedelta(days=14 + random.randint(0, 3)),
            truck_distance_km=round(random.uniform(300, 800), 1),
            sea_distance_nm=round(random.uniform(800, 2500), 1),
            total_delay_hours=round(random.uniform(0, 12), 1) if idx > 0 else 0,
            route_optimization_count=random.randint(0, 3),
            created_at=created,
        )
        shipments.append(s)

    db.session.bulk_save_objects(shipments)
    db.session.commit()
    print(f"✅ Seeded 25 shipments")


def seed_all(app):
    with app.app_context():
        try:
            seed_users()
            seed_ports()
            seed_shipments()
            print("✅ All seed data loaded")
        except Exception as e:
            print(f"⚠️ Seed error: {e}")
            db.session.rollback()
