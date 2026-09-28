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

ML_RESULTS_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml_test_results.csv"
)

BEHAVIORAL_RESULTS_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "behavioral_test_results.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "combined_results.csv"
)


# ============================================================
# LOAD RESULTS
# ============================================================

print("\n================================")
print("       COMBINED DETECTOR")
print("================================")

ml_df = pd.read_csv(ML_RESULTS_PATH)
behavioral_df = pd.read_csv(BEHAVIORAL_RESULTS_PATH)

print(f"\nML result records         : {len(ml_df)}")
print(f"Behavioural result records: {len(behavioral_df)}")


# ============================================================
# VALIDATION
# ============================================================

if len(ml_df) != len(behavioral_df):
    raise ValueError(
        "ML and behavioural result files "
        "have different numbers of rows."
    )

required_ml_columns = [
    "user_id",
    "ml_anomaly",
    "ml_probability",
]

required_behavioral_columns = [
    "user_id",
    "unusual_location",
    "unusual_device",
    "behavioral_anomaly",
]

for column in required_ml_columns:
    if column not in ml_df.columns:
        raise ValueError(
            f"Missing column in ML results: {column}"
        )

for column in required_behavioral_columns:
    if column not in behavioral_df.columns:
        raise ValueError(
            f"Missing column in behavioural results: {column}"
        )

print("\n✓ Result files validated")


# ============================================================
# CHECK ROW ALIGNMENT
# ============================================================

if not ml_df["user_id"].equals(
    behavioral_df["user_id"]
):
    raise ValueError(
        "ML and behavioural results are not aligned."
    )

if not ml_df["is_anomaly"].equals(
    behavioral_df["is_anomaly"]
):
    raise ValueError(
        "Ground truth does not match between "
        "ML and behavioural results."
    )

print("✓ Test records are aligned")


# ============================================================
# COMBINE RESULTS
# ============================================================

combined_df = ml_df.copy()

combined_df["unusual_location"] = (
    behavioral_df["unusual_location"]
)

combined_df["unusual_device"] = (
    behavioral_df["unusual_device"]
)

combined_df["behavioral_anomaly"] = (
    behavioral_df["behavioral_anomaly"]
)


# ============================================================
# FINAL COMBINED PREDICTION
# ============================================================

combined_df["combined_anomaly"] = (
    (combined_df["ml_anomaly"] == 1)
    |
    (combined_df["behavioral_anomaly"] == 1)
).astype(int)


# ============================================================
# ALERT REASON
# ============================================================

def generate_reason(row):

    reasons = []

    if row["ml_anomaly"] == 1:
        reasons.append("ML suspicious access pattern")

    if row["unusual_location"] == 1:
        reasons.append("Unusual location")

    if row["unusual_device"] == 1:
        reasons.append("Unusual device")

    if not reasons:
        return "Normal"

    return " + ".join(reasons)


combined_df["alert_reason"] = (
    combined_df.apply(
        generate_reason,
        axis=1
    )
)


# ============================================================
# EVALUATION
# ============================================================

y_true = combined_df["is_anomaly"].astype(int)

y_pred = combined_df["combined_anomaly"]

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
print("       COMBINED RESULTS")
print("================================")

print(
    f"\nActual anomalies : "
    f"{int(y_true.sum())}"
)

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
# SAVE RESULTS
# ============================================================

combined_df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nResults saved to:")

print(OUTPUT_PATH)

print("\n================================")
print("          COMPLETE")
print("================================")