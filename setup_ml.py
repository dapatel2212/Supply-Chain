#!/usr/bin/env python3
"""
setup_ml.py
───────────
Trains all 6 ML models using REAL data from TimescaleDB (port 5433).
Run ONCE before or after docker-compose up.

Usage:
    python setup_ml.py

Requirements:
    pip install psycopg2-binary sqlalchemy pandas scikit-learn joblib
"""

import os
import sys

# ── TimescaleDB connection URL ─────────────────────────────────────────────────
TIMESCALE_URL = os.getenv(
    "TIMESCALE_URL",
    "postgresql://postgres:Dhairya%402212@localhost:5433/supply_chain"
)


def setup_ml():
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, backend_path)

    print("=" * 60)
    print("  ShipTrack AI — ML Training from Real PostgreSQL Data")
    print("=" * 60)
    print(f"\n  TimescaleDB : {TIMESCALE_URL.split('@')[-1]}")
    print("  Tables      : supply_chain + international_supply_chain")
    print("  Models      : 6 (ETA, Delay, Sea, Port, Route, Risk)\n")

    try:
        from ml.train_from_db import train_from_database
        metrics = train_from_database(TIMESCALE_URL)

        print("\n" + "=" * 60)
        print("  ✅  TRAINING COMPLETE — Model Accuracy Summary")
        print("=" * 60)
        for name, m in metrics.items():
            print(f"  • {name:<25} {m}")
        print("=" * 60 + "\n")
        return True

    except ConnectionError as e:
        print(f"\n❌  Database connection failed:\n    {e}")
        print("\n  → Make sure TimescaleDB is running:")
        print("    docker ps   # should show 'timescaledb' on port 5433")
        return False

    except Exception as e:
        import traceback
        print(f"\n❌  Unexpected error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = setup_ml()
    sys.exit(0 if ok else 1)
