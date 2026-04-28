#!/bin/bash
set -e

echo "🚀 ShipTrack AI - Ubuntu/Mac Setup"

if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 required"
  exit 1
fi

echo "📦 Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install

echo "🗄️ Creating PostgreSQL database..."
createdb shipment_db -U admin 2>/dev/null || echo "Database already exists"

echo "🌱 Initializing database..."
cd ../backend
python3 -c "from database.db_setup import db; from app import create_app; app = create_app()"

echo "✅ Setup complete!"
echo ""
echo "To start services:"
echo "  Backend:  cd backend && source venv/bin/activate && python app.py"
echo "  Frontend: cd frontend && npm start"
echo "  Or use: docker-compose up --build"
