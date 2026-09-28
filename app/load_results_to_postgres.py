import pandas as pd
from sqlalchemy import text

from app.database import engine


CSV_PATH = "data/processed/combined_results.csv"


def load_data():

    # Load combined detection results
    df = pd.read_csv(CSV_PATH)

    print(f"✓ Loaded {len(df)} events from CSV")

    # --------------------------------------------------
    # 1. Load ALL events into access_events
    # --------------------------------------------------

    event_columns = [
        "user_id",
        "timestamp",
        "dataset_name",
        "action",
        "records_accessed",
        "source_ip",
        "location",
        "device",
        "success",
        "ml_anomaly",
        "ml_probability",
        "behavioral_anomaly",
        "combined_anomaly",
        "alert_reason"
    ]

    events = df[event_columns].copy()

    events.to_sql(
        "access_events",
        engine,
        if_exists="append",
        index=False
    )

    print(f"✓ Inserted {len(events)} events into access_events")

    # --------------------------------------------------
    # 2. Load ONLY alerts into security_alerts
    # --------------------------------------------------

    alerts = df[df["combined_anomaly"] == 1][event_columns].copy()

    # Get the IDs of the newly inserted events
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT id
                FROM access_events
                ORDER BY id DESC
                LIMIT :limit
            """),
            {"limit": len(events)}
        )

        event_ids = [row[0] for row in result.fetchall()]

    # Reverse because IDs were retrieved newest → oldest
    event_ids.reverse()

    alerts["event_id"] = [
        event_ids[i]
        for i in alerts.index
    ]

    alert_columns = [
        "event_id",
        "user_id",
        "timestamp",
        "dataset_name",
        "action",
        "records_accessed",
        "source_ip",
        "location",
        "device",
        "ml_anomaly",
        "ml_probability",
        "behavioral_anomaly",
        "combined_anomaly",
        "alert_reason"
    ]

    alerts = alerts[alert_columns]

    alerts.to_sql(
        "security_alerts",
        engine,
        if_exists="append",
        index=False
    )

    print(f"✓ Inserted {len(alerts)} alerts into security_alerts")

    print("\n✓ Data successfully loaded into PostgreSQL")


if __name__ == "__main__":
    load_data()