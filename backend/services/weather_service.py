import os
import requests

OPENWEATHER_KEY = os.getenv('OPENWEATHER_API_KEY')

class WeatherService:
    def get_weather(self, lat: float, lng: float) -> dict:
        if not OPENWEATHER_KEY or not lat:
            return {'condition': 'clear', 'temp': 28, 'wind_speed': 10, 'risk_score': 0}
        try:
            r = requests.get(
                'https://api.openweathermap.org/data/2.5/weather',
                params={'lat': lat, 'lon': lng, 'appid': OPENWEATHER_KEY, 'units': 'metric'},
                timeout=5
            )
            data = r.json()
            wid = data['weather'][0]['id']

            if 200 <= wid < 300:
                cond, risk = 'storm', 90
            elif wid in [503, 504]:
                cond, risk = 'heavy_rain', 70
            elif 500 <= wid < 600:
                cond, risk = 'rain', 40
            elif 600 <= wid < 700:
                cond, risk = 'fog', 50
            elif wid == 800:
                cond, risk = 'clear', 0
            else:
                cond, risk = 'cloudy', 10

            wind = data['wind']['speed'] * 3.6
            if wind > 60: risk += 30
            elif wind > 40: risk += 15

            return {
                'condition': cond,
                'temp': data['main']['temp'],
                'wind_speed_kmph': round(wind, 1),
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'risk_score': min(100, risk),
                'is_severe': risk >= 60
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            return {'condition': 'clear', 'temp': 28, 'wind_speed_kmph': 10, 'risk_score': 0}
