"""
train_from_db.py
────────────────
Loads REAL data from TimescaleDB (port 5433) and trains all 6 ML models.
Tables used:
  • supply_chain                – domestic road shipments (India, 1M rows)
  • international_supply_chain  – global sea freight (500K rows)
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
)
from sklearn.metrics import mean_absolute_error, accuracy_score, r2_score

# ── paths ──────────────────────────────────────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR,   exist_ok=True)

# ── TimescaleDB connection (port 5433) ─────────────────────────────────────────
TIMESCALE_URL = os.getenv(
    "TIMESCALE_URL",
    "postgresql://postgres:Dhairya%402212@localhost:5433/supply_chain"
)


# ══════════════════════════════════════════════════════════════════════════════
# 1.  DATA LOADERS
# ══════════════════════════════════════════════════════════════════════════════

def _congestion_level(value: float) -> str:
    """Map a numeric congestion index (0-1) to a categorical level."""
    if value < 0.25:   return "low"
    if value < 0.50:   return "normal"
    if value < 0.75:   return "high"
    return "critical"


def _weather_from_code(code: str) -> str:
    """Map weather_code string from domestic CSV to model weather categories."""
    if pd.isna(code):
        return "clear"
    code = str(code).lower()
    if "storm" in code:               return "storm"
    if "heavy" in code or "hail" in code: return "heavy_rain"
    if "rain" in code:                return "rain"
    if "fog"  in code or "mist" in code:  return "fog"
    if "cloud" in code or "overcast" in code: return "cloudy"
    return "clear"


def load_domestic_data(engine, sample: int = 300_000) -> pd.DataFrame:
    """
    Load domestic road data from `supply_chain` table and map it to
    the standard training schema expected by eta_model.py.
    """
    print(f"  📦 Loading domestic road data (sample={sample:,}) …")
    query = f"""
        SELECT
            origin_city,
            destination_city,
            carrier_id,
            cargo_type,
            snapshot_timestamp,
            distance_covered_km,
            distance_remaining_km,
            avg_speed_kmh,
            expected_speed_kmh,
            dwell_time_hrs,
            delay_hours_current,
            actual_delay_hrs,
            disruption_flag,
            alternate_routes_avail,
            segment_congestion_idx,
            port_congestion_idx,
            weather_code
        FROM supply_chain
        TABLESAMPLE SYSTEM(30)
        LIMIT {sample}
    """
    df = pd.read_sql(query, engine)
    print(f"     Loaded {len(df):,} rows")

    # ── derive features ──────────────────────────────────────────────────────
    df["total_km"] = df["distance_covered_km"].fillna(0) + df["distance_remaining_km"].fillna(0)
    df["total_km"] = df["total_km"].clip(lower=50)

    # Approximate truck hours = total_km / avg_speed (fallback 50 km/h)
    speed = df["avg_speed_kmh"].replace(0, np.nan).fillna(50)
    df["actual_truck_hours"] = (df["total_km"] / speed).clip(upper=200)

    df["actual_sea_hours"]             = 0.0
    df["actual_origin_port_hours"]     = df["dwell_time_hrs"].fillna(2).clip(0, 48)
    df["actual_destination_port_hours"]= df["dwell_time_hrs"].fillna(2).clip(0, 48)
    df["actual_total_hours"]           = (
        df["actual_truck_hours"] +
        df["actual_origin_port_hours"] +
        df["actual_destination_port_hours"]
    ).clip(1, 500)

    df["was_delayed"]           = df["disruption_flag"].fillna(0).astype(int)
    df["total_delay_hours"]     = df["actual_delay_hrs"].fillna(0).clip(0, 200)
    df["route_optimizations_count"] = df["alternate_routes_avail"].fillna(0).astype(int)

    # Map to model schema
    df["origin_port_code"]      = df["origin_city"].str[:3].str.upper().fillna("UNK") + "IND"
    df["destination_port_code"] = df["destination_city"].str[:3].str.upper().fillna("UNK") + "IND"
    df["weight_tons"]           = np.random.uniform(5, 40, len(df)).round(2)  # not in domestic data
    df["truck_distance_km"]     = df["total_km"]
    df["sea_distance_nm"]       = 0.0

    ts = pd.to_datetime(df["snapshot_timestamp"], errors="coerce")
    df["departure_hour"]        = ts.dt.hour.fillna(8).astype(int)
    df["departure_day_of_week"] = ts.dt.dayofweek.fillna(0).astype(int)
    df["departure_month"]       = ts.dt.month.fillna(1).astype(int)

    df["weather_condition"]     = df["weather_code"].apply(_weather_from_code)
    df["origin_congestion"]     = df["segment_congestion_idx"].fillna(0.3).apply(_congestion_level)
    df["destination_congestion"]= df["port_congestion_idx"].fillna(0.3).apply(_congestion_level)
    df["delay_reason"]          = df["was_delayed"].map({1: "traffic", 0: "none"})

    return df[_SCHEMA_COLS].dropna(subset=["actual_total_hours"])


def load_international_data(engine, sample: int = 200_000) -> pd.DataFrame:
    """
    Load international sea freight data from `international_supply_chain` table.
    """
    print(f"  🚢 Loading international sea data (sample={sample:,}) …")
    query = f"""
        SELECT
            origin_port_code,
            destination_port_code,
            cargo_type,
            cargo_weight_kg,
            total_distance_km,
            actual_speed_kmh,
            dwell_time_hrs,
            avg_dwell_7d_hrs,
            delay_hours_current,
            actual_delay_hrs,
            disruption_flag,
            alt_route_needed,
            dest_port_congestion_idx,
            chokepoint_congestion_idx,
            weather_event_flag,
            wave_height_m,
            departure_datetime,
            snapshot_timestamp
        FROM international_supply_chain
        TABLESAMPLE SYSTEM(40)
        LIMIT {sample}
    """
    df = pd.read_sql(query, engine)
    print(f"     Loaded {len(df):,} rows")

    # ── derive features ──────────────────────────────────────────────────────
    df["weight_tons"]       = (df["cargo_weight_kg"].fillna(20000) / 1000).clip(1, 500)
    df["truck_distance_km"] = 150.0           # port access road (approx)
    df["sea_distance_nm"]   = (df["total_distance_km"].fillna(5000) * 0.539957).clip(100)

    # Sea hours = distance_nm / speed_knots; speed_kmh → knots (/1.852)
    knots = (df["actual_speed_kmh"].replace(0, np.nan).fillna(20) / 1.852).clip(5, 40)
    df["actual_sea_hours"]             = (df["sea_distance_nm"] / knots).clip(10, 1000)
    df["actual_truck_hours"]           = df["truck_distance_km"] / 50
    df["actual_origin_port_hours"]     = df["dwell_time_hrs"].fillna(24).clip(1, 200)
    df["actual_destination_port_hours"]= df["avg_dwell_7d_hrs"].fillna(24).clip(1, 200)
    df["actual_total_hours"]           = (
        df["actual_truck_hours"] +
        df["actual_origin_port_hours"] +
        df["actual_sea_hours"] +
        df["actual_destination_port_hours"]
    ).clip(10, 2000)

    df["was_delayed"]               = df["disruption_flag"].fillna(0).astype(int)
    df["total_delay_hours"]         = df["actual_delay_hrs"].fillna(0).clip(0, 500)
    df["route_optimizations_count"] = df["alt_route_needed"].fillna(0).astype(int)

    # Weather: combine flag + wave height
    def sea_weather(row):
        if row["weather_event_flag"] == 1:
            h = row["wave_height_m"] if not pd.isna(row["wave_height_m"]) else 1
            if h > 4:   return "storm"
            if h > 2.5: return "heavy_rain"
            return "rain"
        return "clear"
    df["weather_condition"] = df.apply(sea_weather, axis=1)

    df["origin_congestion"]      = df["chokepoint_congestion_idx"].fillna(0.2).apply(_congestion_level)
    df["destination_congestion"] = df["dest_port_congestion_idx"].fillna(0.2).apply(_congestion_level)

    dep = pd.to_datetime(df["departure_datetime"], errors="coerce")
    df["departure_hour"]        = dep.dt.hour.fillna(8).astype(int)
    df["departure_day_of_week"] = dep.dt.dayofweek.fillna(0).astype(int)
    df["departure_month"]       = dep.dt.month.fillna(1).astype(int)

    df["delay_reason"] = df["was_delayed"].map({1: "port_congestion", 0: "none"})

    return df[_SCHEMA_COLS].dropna(subset=["actual_total_hours"])


# Canonical column list the model pipeline expects
_SCHEMA_COLS = [
    "origin_port_code", "destination_port_code", "cargo_type",
    "weight_tons", "truck_distance_km", "sea_distance_nm",
    "departure_hour", "departure_day_of_week", "departure_month",
    "weather_condition", "origin_congestion", "destination_congestion",
    "actual_truck_hours", "actual_origin_port_hours",
    "actual_sea_hours", "actual_destination_port_hours",
    "actual_total_hours", "was_delayed", "total_delay_hours",
    "delay_reason", "route_optimizations_count",
]


# ══════════════════════════════════════════════════════════════════════════════
# 2.  MODEL PIPELINE  (same architecture as original eta_model.py)
# ══════════════════════════════════════════════════════════════════════════════

class ShipTrackMLPipeline:
    def __init__(self):
        self.models   = {}
        self.encoders = {}

    def _encode(self, df: pd.DataFrame, cat_cols: list) -> pd.DataFrame:
        df = df.copy()
        for c in cat_cols:
            if c not in self.encoders:
                self.encoders[c] = LabelEncoder()
                df[c] = self.encoders[c].fit_transform(df[c].astype(str))
            else:
                known = set(self.encoders[c].classes_)
                df[c] = df[c].astype(str).apply(
                    lambda x: x if x in known else self.encoders[c].classes_[0]
                )
                df[c] = self.encoders[c].transform(df[c])
        return df

    # ── individual trainers ────────────────────────────────────────────────
    def train_eta_model(self, df):
        cat_cols = ["origin_port_code", "destination_port_code", "cargo_type",
                    "weather_condition", "origin_congestion", "destination_congestion"]
        num_cols = ["weight_tons", "truck_distance_km", "sea_distance_nm",
                    "departure_hour", "departure_day_of_week", "departure_month"]
        features = cat_cols + num_cols
        df_enc = self._encode(df, cat_cols)
        X, y = df_enc[features], df_enc["actual_total_hours"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=150, max_depth=6, random_state=42)
        model.fit(Xtr, ytr)
        preds = model.predict(Xte)
        mae, r2 = mean_absolute_error(yte, preds), r2_score(yte, preds)
        joblib.dump({"model": model, "features": features, "encoders": self.encoders},
                    os.path.join(MODELS_DIR, "eta_prediction.pkl"))
        return {"mae_hours": round(mae, 2), "r2_score": round(r2, 3)}

    def train_delay_model(self, df):
        cat_cols = ["origin_port_code", "destination_port_code", "cargo_type",
                    "weather_condition", "origin_congestion", "destination_congestion"]
        num_cols = ["weight_tons", "truck_distance_km", "sea_distance_nm",
                    "departure_hour", "departure_day_of_week", "departure_month"]
        features = cat_cols + num_cols
        df_enc = self._encode(df, cat_cols)
        X, y = df_enc[features], df_enc["was_delayed"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
        model.fit(Xtr, ytr)
        acc = accuracy_score(yte, model.predict(Xte))
        joblib.dump({"model": model, "features": features, "encoders": self.encoders},
                    os.path.join(MODELS_DIR, "delay_detection.pkl"))
        return {"accuracy": round(acc, 3)}

    def train_sea_duration(self, df):
        sea_df = df[df["sea_distance_nm"] > 0].copy()
        if len(sea_df) < 100:
            sea_df = df.copy()
        cat_cols = ["origin_port_code", "destination_port_code", "weather_condition"]
        features = cat_cols + ["sea_distance_nm", "departure_month"]
        df_enc = self._encode(sea_df, cat_cols)
        X, y = df_enc[features], df_enc["actual_sea_hours"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(Xtr, ytr)
        mae = mean_absolute_error(yte, model.predict(Xte))
        joblib.dump({"model": model, "features": features, "encoders": self.encoders},
                    os.path.join(MODELS_DIR, "sea_duration.pkl"))
        return {"mae_hours": round(mae, 2)}

    def train_port_processing(self, df):
        cat_cols = ["destination_port_code", "destination_congestion", "cargo_type"]
        features = cat_cols + ["weight_tons"]
        df_enc = self._encode(df, cat_cols)
        X, y = df_enc[features], df_enc["actual_destination_port_hours"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(Xtr, ytr)
        mae = mean_absolute_error(yte, model.predict(Xte))
        joblib.dump({"model": model, "features": features, "encoders": self.encoders},
                    os.path.join(MODELS_DIR, "port_processing.pkl"))
        return {"mae_hours": round(mae, 2)}

    def train_route_optimizer(self, df):
        cat_cols = ["weather_condition", "origin_congestion", "destination_congestion"]
        features = cat_cols + ["truck_distance_km", "sea_distance_nm"]
        df_enc = self._encode(df, cat_cols)
        X = df_enc[features]
        y = (df_enc["route_optimizations_count"] > 0).astype(int)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(Xtr, ytr)
        acc = accuracy_score(yte, model.predict(Xte))
        joblib.dump({"model": model, "features": features, "encoders": self.encoders},
                    os.path.join(MODELS_DIR, "route_optimizer.pkl"))
        return {"accuracy": round(acc, 3)}

    def train_risk_assessment(self, df):
        cat_cols = ["origin_port_code", "destination_port_code", "weather_condition",
                    "origin_congestion", "destination_congestion"]
        features = cat_cols + ["weight_tons", "truck_distance_km", "sea_distance_nm"]
        df_enc = self._encode(df, cat_cols)
        X, y = df_enc[features], df_enc["total_delay_hours"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model.fit(Xtr, ytr)
        mae = mean_absolute_error(yte, model.predict(Xte))
        joblib.dump({"model": model, "features": features, "encoders": self.encoders},
                    os.path.join(MODELS_DIR, "risk_assessment.pkl"))
        return {"mae_hours": round(mae, 2)}


# ══════════════════════════════════════════════════════════════════════════════
# 3.  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def train_from_database(timescale_url: str = None) -> dict:
    """
    Full pipeline: load both CSVs from TimescaleDB → combine → train 6 models.
    """
    url = timescale_url or TIMESCALE_URL
    print(f"\n🔌 Connecting to TimescaleDB: {url.split('@')[-1]}")

    try:
        engine = create_engine(url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            print("✅ Connected to TimescaleDB\n")
    except Exception as e:
        raise ConnectionError(f"Cannot connect to TimescaleDB: {e}\n"
                              "Check that TimescaleDB is running on port 5433 "
                              "and TIMESCALE_URL is correct.")

    # ── load both tables ───────────────────────────────────────────────────
    domestic = load_domestic_data(engine)
    intl     = load_international_data(engine)

    df = pd.concat([domestic, intl], ignore_index=True)
    df = df.dropna(subset=["actual_total_hours", "was_delayed"])
    print(f"\n📊 Combined dataset: {len(df):,} rows, {len(df.columns)} columns")

    # Cache locally for reproducibility
    cache_path = os.path.join(DATA_DIR, "training_data_from_db.csv")
    df.to_csv(cache_path, index=False)
    print(f"💾 Cached training data → {cache_path}\n")

    # ── train ──────────────────────────────────────────────────────────────
    pipeline = ShipTrackMLPipeline()
    metrics  = {}

    steps = [
        ("ETA Prediction",       pipeline.train_eta_model,        "eta"),
        ("Delay Detection",      pipeline.train_delay_model,       "delay"),
        ("Sea Duration",         pipeline.train_sea_duration,      "sea_duration"),
        ("Port Processing",      pipeline.train_port_processing,   "port_processing"),
        ("Route Optimizer",      pipeline.train_route_optimizer,   "route_optimizer"),
        ("Risk Assessment",      pipeline.train_risk_assessment,   "risk_assessment"),
    ]
    for label, fn, key in steps:
        print(f"  🤖 [{key}] Training {label} …")
        metrics[key] = fn(df)
        print(f"        Result: {metrics[key]}")

    # Save accuracy report
    report_path = os.path.join(MODELS_DIR, "accuracy_report.json")
    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ All 6 models trained on REAL data and saved to {MODELS_DIR}")
    print(f"📊 Accuracy report → {report_path}\n")
    return metrics


if __name__ == "__main__":
    train_from_database()
