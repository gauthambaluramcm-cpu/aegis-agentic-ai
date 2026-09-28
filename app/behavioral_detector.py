from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "train.csv"
)

TEST_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "test.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "behavioral_test_results.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("\n================================")
print("     BEHAVIOURAL DETECTOR")
print("================================")

train_df = pd.read_csv(TRAIN_PATH)
test_df = pd.read_csv(TEST_PATH)

print(f"\nTraining records: {len(train_df)}")
print(f"Testing records : {len(test_df)}")


# ============================================================
# VALIDATION
# ============================================================

required_columns = [
    "user_id",
    "location",
    "device",
    "is_anomaly",
    "anomaly_type",
]

for column in required_columns:
    if column not in train_df.columns:
        raise ValueError(
            f"Missing column in train.csv: {column}"
        )

    if column not in test_df.columns:
        raise ValueError(
            f"Missing column in test.csv: {column}"
        )

print("\n✓ Required columns validated")


# ============================================================
# BUILD NORMAL USER PROFILES
# ============================================================

print("\nBuilding user behaviour profiles...")

user_locations = (
    train_df
    .groupby("user_id")["location"]
    .apply(set)
    .to_dict()
)

user_devices = (
    train_df
    .groupby("user_id")["device"]
    .apply(set)
    .to_dict()
)


# ============================================================
# DETECTION
# ============================================================

test_df["unusual_location"] = 0
test_df["unusual_device"] = 0


for index, row in test_df.iterrows():

    user = row["user_id"]
    location = row["location"]
    device = row["device"]

    known_locations = user_locations.get(
        user,
        set()
    )

    known_devices = user_devices.get(
        user,
        set()
    )

    if location not in known_locations:
        test_df.at[
            index,
            "unusual_location"
        ] = 1

    if device not in known_devices:
        test_df.at[
            index,
            "unusual_device"
        ] = 1


# ============================================================
# FINAL BEHAVIOURAL PREDICTION
# ============================================================

test_df["behavioral_anomaly"] = (
    (test_df["unusual_location"] == 1)
    |
    (test_df["unusual_device"] == 1)
).astype(int)


# ============================================================
# EVALUATION
# ============================================================

y_true = test_df["is_anomaly"].astype(int)

y_pred = test_df["behavioral_anomaly"]


precision = precision_score(
    y_true,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0,
)


print("\n================================")
print("       RESULTS")
print("================================")

print(f"\nActual anomalies : {int(y_true.sum())}")

print(
    f"Detected         : "
    f"{int(((y_true == 1) & (y_pred == 1)).sum())}"
)

print(
    f"False alarms     : "
    f"{int(((y_true == 0) & (y_pred == 1)).sum())}"
)

print(f"\nPrecision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_true,
        y_pred
    )
)


# ============================================================
# ANOMALY TYPE ANALYSIS
# ============================================================

print("\n================================")
print("     ANOMALY TYPE ANALYSIS")
print("================================")


anomaly_df = test_df[
    test_df["is_anomaly"] == 1
].copy()


for anomaly_type in sorted(
    anomaly_df["anomaly_type"].unique()
):

    subset = anomaly_df[
        anomaly_df["anomaly_type"]
        == anomaly_type
    ]

    detected = int(
        subset["behavioral_anomaly"].sum()
    )

    total = len(subset)

    missed = total - detected

    recall_type = (
        detected / total
        if total > 0
        else 0
    )

    print(
        f"{anomaly_type:<18} "
        f"{detected} detected / "
        f"{missed} missed / "
        f"recall {recall_type:.4f}"
    )


# ============================================================
# SAVE RESULTS
# ============================================================

test_df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nResults saved to:")

print(OUTPUT_PATH)

print("\n================================")
print("          COMPLETE")
print("================================")