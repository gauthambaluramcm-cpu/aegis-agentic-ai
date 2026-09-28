from pathlib import Path
from datetime import datetime, timedelta

import random
import pandas as pd


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42

TOTAL_LOGS = 20_000
ANOMALY_RATE = 0.05

NORMAL_LOGS = int(TOTAL_LOGS * (1 - ANOMALY_RATE))
ANOMALY_LOGS = int(TOTAL_LOGS * ANOMALY_RATE)

print(f"Total logs: {TOTAL_LOGS}")
print(f"Normal logs: {NORMAL_LOGS}")
print(f"Anomalous logs: {ANOMALY_LOGS}")


# --------------------------------------------------
# RANDOMNESS
# --------------------------------------------------

random.seed(SEED)


# --------------------------------------------------
# DATA PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# NORMAL BEHAVIOUR CONFIGURATION
# --------------------------------------------------

NORMAL_ACTIONS = [
    "SELECT",
    "SELECT",
    "SELECT",
    "UPDATE"
]

NORMAL_DATASETS = [
    "customers",
    "employees",
    "users"
]

NORMAL_DEVICES = [
    "Laptop",
    "Desktop"
]

NORMAL_LOCATIONS = [
    "Bangalore",
    "Mumbai",
    "Delhi",
    "Chennai",
    "Hyderabad",
    "Pune"
]

# --------------------------------------------------
# USER BEHAVIOUR PROFILES
# --------------------------------------------------

USERS_FILE = RAW_DATA_DIR / "users.csv"


# --------------------------------------------------
# USER BEHAVIOUR PROFILES
# --------------------------------------------------

USERS_FILE = RAW_DATA_DIR / "users.csv"


def load_user_profiles():

    users_df = pd.read_csv(USERS_FILE)

    profiles = {}

    for _, row in users_df.iterrows():

        profiles[row["user_id"]] = {
            "normal_location": row["location"],
            "normal_device": random.choice(
                ["Laptop", "Desktop"]
            ),
            "access_level": row["access_level"],
            "department": row["department"],
            "role": row["role"]
        }

    return profiles


USER_PROFILES = load_user_profiles()
# --------------------------------------------------
# NORMAL ACCESS EVENT
# --------------------------------------------------

def generate_normal_event(
    user_id,
    timestamp,
    location=None,
    device=None
):

    profile = USER_PROFILES.get(user_id)

    if location is None:
      if profile:
        location = profile["normal_location"]
      else:
        location = random.choice(NORMAL_LOCATIONS)

    if device is None:
      if profile:
        device = profile["normal_device"]
      else:
        device = random.choice(NORMAL_DEVICES)

    dataset = random.choice(NORMAL_DATASETS)

    action = random.choice(NORMAL_ACTIONS)

    # Normal users usually access relatively
    # small numbers of records.
    records_accessed = random.randint(1, 50)

    # Synthetic private-network IP.
    source_ip = (
        f"10."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "dataset_name": dataset,
        "action": action,
        "records_accessed": records_accessed,
        "source_ip": source_ip,
        "location": location,
        "device": device,
        "success": True
    }
def generate_bulk_access_event(user_id, timestamp):

    source_ip = (
        f"10."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "dataset_name": "customers",
        "action": "EXPORT",
        "records_accessed": random.randint(5000, 10000),
        "source_ip": source_ip,
        "location": random.choice(NORMAL_LOCATIONS),
        "device": random.choice(NORMAL_DEVICES),
        "success": True
    }

def generate_unusual_time_event(user_id):

    # Deliberately generate access during
    # unusual hours (midnight to 5 AM).

    hour = random.randint(0, 5)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    timestamp = datetime(
        2026,
        8,
        random.randint(1, 30),
        hour,
        minute,
        second
    )

    source_ip = (
        f"10."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "dataset_name": random.choice(NORMAL_DATASETS),
        "action": "SELECT",
        "records_accessed": random.randint(1, 50),
        "source_ip": source_ip,
        "location": random.choice(NORMAL_LOCATIONS),
        "device": random.choice(NORMAL_DEVICES),
        "success": True
    }
# --------------------------------------------------
# NORMAL BUSINESS HOURS
# --------------------------------------------------

def generate_normal_timestamp(start_date):

    days_offset = random.randint(0, 29)

    hour = random.randint(9, 17)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return (
        start_date
        + timedelta(days=days_offset)
        + timedelta(
            hours=hour,
            minutes=minute,
            seconds=second
        )
    )
def generate_unusual_location_event(user_id):

    profile = USER_PROFILES.get(user_id)

    if profile:
        normal_location = profile["normal_location"]

        unusual_locations = [
            location
            for location in NORMAL_LOCATIONS
            if location != normal_location
        ]

        location = random.choice(unusual_locations)

        device = profile["normal_device"]

    else:
        location = random.choice(NORMAL_LOCATIONS)
        device = random.choice(NORMAL_DEVICES)

    timestamp = generate_normal_timestamp(
        datetime(2026, 8, 1)
    )

    source_ip = (
        f"10."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "dataset_name": random.choice(NORMAL_DATASETS),
        "action": "SELECT",
        "records_accessed": random.randint(1, 50),
        "source_ip": source_ip,
        "location": location,
        "device": device,
        "success": True
    }
def generate_unusual_device_event(user_id):

    profile = USER_PROFILES.get(user_id)

    if profile:
        normal_device = profile["normal_device"]

        devices = [
            "Laptop",
            "Desktop",
            "Mobile",
            "Tablet",
            "Unknown Device"
        ]

        unusual_devices = [
            device
            for device in devices
            if device != normal_device
        ]

        device = random.choice(unusual_devices)

        location = profile["normal_location"]

    else:
        device = "Unknown Device"
        location = random.choice(NORMAL_LOCATIONS)

    timestamp = generate_normal_timestamp(
        datetime(2026, 8, 1)
    )

    source_ip = (
        f"10."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "dataset_name": random.choice(NORMAL_DATASETS),
        "action": "SELECT",
        "records_accessed": random.randint(1, 50),
        "source_ip": source_ip,
        "location": location,
        "device": device,
        "success": True
    }

def generate_failed_access_event(user_id):

    profile = USER_PROFILES.get(user_id)

    if profile:
        location = profile["normal_location"]
        device = profile["normal_device"]
    else:
        location = random.choice(NORMAL_LOCATIONS)
        device = random.choice(NORMAL_DEVICES)

    timestamp = generate_normal_timestamp(
        datetime(2026, 8, 1)
    )

    source_ip = (
        f"10."
        f"{random.randint(0, 255)}."
        f"{random.randint(0, 255)}."
        f"{random.randint(1, 254)}"
    )

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "dataset_name": random.choice(NORMAL_DATASETS),
        "action": "SELECT",
        "records_accessed": 0,
        "source_ip": source_ip,
        "location": location,
        "device": device,
        "success": False
    }

# --------------------------------------------------
# MASTER ACCESS LOG GENERATOR
# --------------------------------------------------

def generate_all_access_logs():

    start_date = datetime(2026, 8, 1)

    events = []
    ground_truth = []

    user_ids = list(USER_PROFILES.keys())

    # ----------------------------------------------
    # 1. GENERATE NORMAL EVENTS
    # ----------------------------------------------

    for _ in range(NORMAL_LOGS):

        user_id = random.choice(user_ids)

        timestamp = generate_normal_timestamp(start_date)

        event = generate_normal_event(
            user_id=user_id,
            timestamp=timestamp
        )

        events.append(event)

        ground_truth.append({
            "event_index": len(events),
            "is_anomaly": 0,
            "anomaly_type": "NORMAL"
        })

    # ----------------------------------------------
    # 2. GENERATE ANOMALOUS EVENTS
    # ----------------------------------------------

    anomaly_generators = [
        ("BULK_ACCESS", generate_bulk_access_event),
        ("UNUSUAL_TIME", generate_unusual_time_event),
        ("UNUSUAL_LOCATION", generate_unusual_location_event),
        ("UNUSUAL_DEVICE", generate_unusual_device_event),
        ("FAILED_ACCESS", generate_failed_access_event),
    ]

    for _ in range(ANOMALY_LOGS):

        user_id = random.choice(user_ids)

        anomaly_type, generator = random.choice(
            anomaly_generators
        )

        if anomaly_type == "BULK_ACCESS":

            timestamp = generate_normal_timestamp(
                start_date
            )

            event = generator(
                user_id=user_id,
                timestamp=timestamp
            )

        elif anomaly_type == "UNUSUAL_TIME":

            event = generator(
                user_id=user_id
            )

        elif anomaly_type == "UNUSUAL_LOCATION":

            event = generator(
                user_id=user_id
            )

        elif anomaly_type == "UNUSUAL_DEVICE":

            event = generator(
                user_id=user_id
            )

        elif anomaly_type == "FAILED_ACCESS":

            event = generator(
                user_id=user_id
            )

        events.append(event)

        ground_truth.append({
            "event_index": len(events),
            "is_anomaly": 1,
            "anomaly_type": anomaly_type
        })

    return events, ground_truth

# --------------------------------------------------
# SAVE DATASETS
# --------------------------------------------------

def save_datasets(events, ground_truth):

    access_logs_df = pd.DataFrame(events)

    ground_truth_df = pd.DataFrame(ground_truth)

    access_logs_path = (
        RAW_DATA_DIR / "access_logs.csv"
    )

    ground_truth_path = (
        GROUND_TRUTH_DIR / "anomaly_ground_truth.csv"
    )

    access_logs_df.to_csv(
        access_logs_path,
        index=False
    )

    ground_truth_df.to_csv(
        ground_truth_path,
        index=False
    )

    print("\n================================")
    print("   DATA GENERATION COMPLETE")
    print("================================")

    print(f"Access logs: {len(access_logs_df)}")
    print(f"Ground truth: {len(ground_truth_df)}")

    print(f"\nAccess logs saved to:")
    print(access_logs_path)

    print(f"\nGround truth saved to:")
    print(ground_truth_path)

if __name__ == "__main__":

    events, ground_truth = generate_all_access_logs()

    save_datasets(
        events,
        ground_truth
    )