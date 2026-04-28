from celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='tasks.tracking_tasks.check_all_active')
def check_all_active():
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from database.db_setup import db, Shipment
            from services.tracking_service import TrackingService
            from services.route_optimizer import RouteOptimizer
            from services.notification_service import NotificationService

            tracker = TrackingService()
            optimizer = RouteOptimizer()
            notifier = NotificationService()

            active = db.session.query(Shipment).filter(
                Shipment.current_status.notin_(['delivered', 'cancelled'])
            ).all()

            logger.info(f"Checking {len(active)} active shipments")

            for s in active:
                try:
                    result = tracker.update_position(s.id)
                    if result and result.get('delay', {}).get('trigger_reoptimize'):
                        delay_hrs = result['delay']['delay_hours']
                        opt = optimizer.reoptimize(s.id, 'auto_system')
                        if opt.get('success'):
                            notifier.send_delay_alert(s, delay_hrs)
                except Exception as e:
                    logger.error(f"Error checking shipment {s.id}: {e}")

            return f"Checked {len(active)} shipments"
    except Exception as e:
        logger.error(f"check_all_active failed: {e}")
        return str(e)

@celery_app.task(name='tasks.tracking_tasks.update_positions')
def update_positions():
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from database.db_setup import db, Shipment
            from services.tracking_service import TrackingService

            tracker = TrackingService()
            active = db.session.query(Shipment).filter(
                Shipment.current_phase.in_(['land_origin', 'sea', 'land_destination'])
            ).all()

            for s in active:
                tracker.update_position(s.id)

            return f"Updated {len(active)} positions"
    except Exception as e:
        logger.error(f"update_positions failed: {e}")
        return str(e)

@celery_app.task(name='tasks.tracking_tasks.retrain_models')
def retrain_models():
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from ml.eta_model import train_all_models
            metrics = train_all_models()
            logger.info(f"Models retrained: {metrics}")
            return "Models retrained successfully"
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        return str(e)
