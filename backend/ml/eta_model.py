import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, accuracy_score, r2_score

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

class ShipTrackMLPipeline:
    def __init__(self):
        self.models = {}
        self.encoders = {}

    def _encode(self, df, cat_cols):
        df = df.copy()
        for c in cat_cols:
            if c not in self.encoders:
                self.encoders[c] = LabelEncoder()
                df[c] = self.encoders[c].fit_transform(df[c].astype(str))
            else:
                df[c] = self.encoders[c].transform(df[c].astype(str))
        return df

    def train_eta_model(self, df):
        cat_cols = ['origin_port_code', 'destination_port_code', 'cargo_type', 'weather_condition', 'origin_congestion', 'destination_congestion']
        features = cat_cols + ['weight_tons', 'truck_distance_km', 'sea_distance_nm', 'departure_hour', 'departure_day_of_week', 'departure_month']
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = df_enc['actual_total_hours']

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
        mae = mean_absolute_error(y_te, preds)
        r2 = r2_score(y_te, preds)

        self.models['eta'] = model
        joblib.dump({'model': model, 'features': features, 'encoders': self.encoders}, os.path.join(MODELS_DIR, 'eta_prediction.pkl'))
        return {'mae_hours': round(mae, 2), 'r2_score': round(r2, 3)}

    def train_delay_model(self, df):
        cat_cols = ['origin_port_code', 'destination_port_code', 'cargo_type', 'weather_condition', 'origin_congestion', 'destination_congestion']
        features = cat_cols + ['weight_tons', 'truck_distance_km', 'sea_distance_nm', 'departure_hour', 'departure_day_of_week', 'departure_month']
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = df_enc['was_delayed']

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, model.predict(X_te))

        self.models['delay'] = model
        joblib.dump({'model': model, 'features': features, 'encoders': self.encoders}, os.path.join(MODELS_DIR, 'delay_detection.pkl'))
        return {'accuracy': round(acc, 3)}

    def train_sea_duration(self, df):
        cat_cols = ['origin_port_code', 'destination_port_code', 'weather_condition']
        features = cat_cols + ['sea_distance_nm', 'departure_month']
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = df_enc['actual_sea_hours']

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=80, random_state=42)
        model.fit(X_tr, y_tr)
        mae = mean_absolute_error(y_te, model.predict(X_te))

        joblib.dump({'model': model, 'features': features, 'encoders': self.encoders}, os.path.join(MODELS_DIR, 'sea_duration.pkl'))
        return {'mae_hours': round(mae, 2)}

    def train_port_processing(self, df):
        cat_cols = ['destination_port_code', 'destination_congestion', 'cargo_type']
        features = cat_cols + ['weight_tons']
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = df_enc['actual_destination_port_hours']

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=80, random_state=42)
        model.fit(X_tr, y_tr)
        mae = mean_absolute_error(y_te, model.predict(X_te))

        joblib.dump({'model': model, 'features': features, 'encoders': self.encoders}, os.path.join(MODELS_DIR, 'port_processing.pkl'))
        return {'mae_hours': round(mae, 2)}

    def train_route_optimizer(self, df):
        cat_cols = ['weather_condition', 'origin_congestion', 'destination_congestion']
        features = cat_cols + ['truck_distance_km', 'sea_distance_nm']
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = (df_enc['route_optimizations_count'] > 0).astype(int)

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=80, random_state=42)
        model.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, model.predict(X_te))

        joblib.dump({'model': model, 'features': features, 'encoders': self.encoders}, os.path.join(MODELS_DIR, 'route_optimizer.pkl'))
        return {'accuracy': round(acc, 3)}

    def train_risk_assessment(self, df):
        cat_cols = ['origin_port_code', 'destination_port_code', 'weather_condition', 'origin_congestion', 'destination_congestion']
        features = cat_cols + ['weight_tons', 'truck_distance_km', 'sea_distance_nm']
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = df_enc['total_delay_hours']

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=80, random_state=42)
        model.fit(X_tr, y_tr)
        mae = mean_absolute_error(y_te, model.predict(X_te))

        joblib.dump({'model': model, 'features': features, 'encoders': self.encoders}, os.path.join(MODELS_DIR, 'risk_assessment.pkl'))
        return {'mae_hours': round(mae, 2)}

    def load_all(self):
        try:
            for name in ['eta_prediction', 'delay_detection', 'sea_duration', 'port_processing', 'route_optimizer', 'risk_assessment']:
                path = os.path.join(MODELS_DIR, f'{name}.pkl')
                if not os.path.exists(path):
                    return False
                self.models[name] = joblib.load(path)
            return True
        except Exception as e:
            print(f"Load error: {e}")
            return False

def train_all_models():
    print("🤖 Training ML Models...")

    csv_path = os.path.join(DATA_DIR, 'training_data.csv')
    if not os.path.exists(csv_path):
        print("⚠️ Training data not found. Generating...")
        from ml.generate_data import ShipmentDataGenerator
        gen = ShipmentDataGenerator()
        df = gen.generate(10000)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    print(f"  Training on {len(df)} samples")

    pipeline = ShipTrackMLPipeline()
    metrics = {}

    print("  [1/6] Training ETA prediction model...")
    metrics['eta'] = pipeline.train_eta_model(df)
    print(f"        MAE: {metrics['eta']['mae_hours']}h, R²: {metrics['eta']['r2_score']}")

    print("  [2/6] Training delay detection model...")
    metrics['delay'] = pipeline.train_delay_model(df)
    print(f"        Accuracy: {metrics['delay']['accuracy']}")

    print("  [3/6] Training sea duration model...")
    metrics['sea_duration'] = pipeline.train_sea_duration(df)

    print("  [4/6] Training port processing model...")
    metrics['port_processing'] = pipeline.train_port_processing(df)

    print("  [5/6] Training route optimizer model...")
    metrics['route_optimizer'] = pipeline.train_route_optimizer(df)

    print("  [6/6] Training risk assessment model...")
    metrics['risk_assessment'] = pipeline.train_risk_assessment(df)

    report_path = os.path.join(MODELS_DIR, 'accuracy_report.json')
    with open(report_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ All 6 models trained and saved to {MODELS_DIR}")
    print(f"📊 Accuracy report: {report_path}")
    return metrics

if __name__ == '__main__':
    train_all_models()
