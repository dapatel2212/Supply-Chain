import pandas as pd
import numpy as np
import random

class ShipmentDataGenerator:
    def __init__(self):
        self.ports = ['INMUN', 'INNSA', 'INMAA', 'AEJEA', 'AEDXB', 'SGSIN', 'CNSHA', 'NLRTM']
        self.cargo_types = ['Rice', 'Textiles', 'Electronics', 'Spices', 'Auto Parts', 'Furniture', 'Chemicals']
        self.weather_conditions = ['clear', 'cloudy', 'rain', 'heavy_rain', 'storm', 'fog']
        self.congestion_levels = ['low', 'normal', 'high', 'critical']

    def generate(self, n=10000):
        np.random.seed(42)
        random.seed(42)

        rows = []
        for _ in range(n):
            origin = random.choice(self.ports)
            dest = random.choice([p for p in self.ports if p != origin])
            cargo = random.choice(self.cargo_types)
            weight = round(np.random.uniform(5, 60), 2)
            truck_km = round(np.random.uniform(200, 1000), 1)
            sea_nm = round(np.random.uniform(500, 5000), 1)

            dep_hour = np.random.randint(0, 24)
            dep_dow = np.random.randint(0, 7)
            dep_month = np.random.randint(1, 13)

            weather = np.random.choice(self.weather_conditions, p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.05])
            o_cong = np.random.choice(self.congestion_levels, p=[0.3, 0.4, 0.2, 0.1])
            d_cong = np.random.choice(self.congestion_levels, p=[0.3, 0.4, 0.2, 0.1])

            truck_h = truck_km / np.random.uniform(45, 65)
            sea_h = sea_nm / np.random.uniform(15, 25)
            origin_port_h = {'low': 12, 'normal': 20, 'high': 30, 'critical': 48}[o_cong]
            dest_port_h = {'low': 10, 'normal': 18, 'high': 28, 'critical': 45}[d_cong]

            weather_mult = {'clear': 1.0, 'cloudy': 1.05, 'rain': 1.15, 'heavy_rain': 1.3, 'storm': 1.6, 'fog': 1.2}[weather]
            sea_h *= weather_mult

            total_h = truck_h + origin_port_h + sea_h + dest_port_h
            delayed = total_h > (truck_km/55 + sea_nm/20 + 30) * 1.1
            delay_h = max(0, total_h - (truck_km/55 + sea_nm/20 + 30)) if delayed else 0

            delay_reason = None
            if delayed:
                if weather in ['storm', 'heavy_rain', 'fog']:
                    delay_reason = 'weather'
                elif o_cong in ['high', 'critical'] or d_cong in ['high', 'critical']:
                    delay_reason = 'port_congestion'
                else:
                    delay_reason = 'traffic'

            rows.append({
                'origin_port_code': origin,
                'destination_port_code': dest,
                'cargo_type': cargo,
                'weight_tons': weight,
                'truck_distance_km': truck_km,
                'sea_distance_nm': sea_nm,
                'departure_hour': dep_hour,
                'departure_day_of_week': dep_dow,
                'departure_month': dep_month,
                'weather_condition': weather,
                'origin_congestion': o_cong,
                'destination_congestion': d_cong,
                'actual_truck_hours': round(truck_h, 2),
                'actual_origin_port_hours': round(origin_port_h, 2),
                'actual_sea_hours': round(sea_h, 2),
                'actual_destination_port_hours': round(dest_port_h, 2),
                'actual_total_hours': round(total_h, 2),
                'was_delayed': int(delayed),
                'total_delay_hours': round(delay_h, 2),
                'delay_reason': delay_reason or 'none',
                'route_optimizations_count': np.random.randint(0, 4),
            })

        return pd.DataFrame(rows)

if __name__ == '__main__':
    import os
    gen = ShipmentDataGenerator()
    df = gen.generate(10000)
    os.makedirs('./data', exist_ok=True)
    df.to_csv('./data/training_data.csv', index=False)
    print(f"✅ Generated {len(df)} samples → ./data/training_data.csv")
