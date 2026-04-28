@echo off
REM ShipTrack AI - Windows Setup

echo 🚀 ShipTrack AI - Windows Setup

where python >nul 2>nul || (
  echo ❌ Python 3 required. Download from python.org
  exit /b 1
)

echo 📦 Installing backend dependencies...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo 📦 Installing frontend dependencies...
cd ..\frontend
call npm install

echo 🗄️ PostgreSQL database setup...
echo Run these commands in PostgreSQL:
echo   CREATE DATABASE shipment_db;

echo 🌱 Initializing database...
cd ..\backend
python -c "from database.db_setup import db; from app import create_app; app = create_app()"

echo ✅ Setup complete!
echo.
echo To start services:
echo   Backend:  cd backend ^&^& venv\Scripts\activate.bat ^&^& python app.py
echo   Frontend: cd frontend ^&^& npm start
echo   Or use: docker-compose up --build
