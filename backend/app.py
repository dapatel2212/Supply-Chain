import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from datetime import timedelta
import json

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://admin:password123@localhost:5432/shipment_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'shiptrack-super-secret-key-change-in-prod')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

    CORS(app)
    JWTManager(app)

    from database.db_setup import db
    db.init_app(app)

    with app.app_context():
        db.create_all()
        
        from database.seed_data import seed_all
        try:
            from database.db_setup import User
            if db.session.query(User).count() == 0:
                print("🌱 Seeding database...")
                seed_all(app)
                print("✅ Database seeded")
        except Exception as e:
            print(f"Seed warning: {e}")

        try:
            from ml.train_from_db import train_from_database as train_all_models
            print("🤖 Checking ML models...")
            train_all_models()
        except Exception as e:
            print(f"ML training warning: {e}")

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy', 'service': 'ShipTrack API'})

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            from database.db_setup import User
            user = db.session.query(User).filter_by(email=data['email']).first()
            
            if not user or not user.verify_password(data['password']):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            access_token = create_access_token(
                identity={'id': user.id, 'email': user.email, 'name': user.name}
            )
            return jsonify({
                'success': True,
                'access_token': access_token,
                'user': user.to_dict()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized access'}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"Server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    from routes.shipment_routes import shipment_bp
    from routes.analytics_routes import analytics_bp
    app.register_blueprint(shipment_bp)
    app.register_blueprint(analytics_bp)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
