from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ACCESS_LOG_PATH = BASE_DIR / "data" / "raw" / "access_logs.csv"

GROUND_TRUTH_PATH = (
    BASE_DIR
    / "data"
    / "ground_truth"
    / "anomaly_ground_truth.csv"
)

TRAIN_OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "train.csv"
)

TEST_OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "test.csv"
)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
    "records_accessed",
    "hour",
    "day_of_week",
    "is_unusual_time",
    "is_export",
    "is_update",
    "is_failed",
    "user_avg_records",
    "user_max_records",
    "user_access_count",
    "user_failed_count",
    "records_vs_user_average",
    "is_bulk_access",
]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features():

    print("\n================================")
    print("   AEGIS FEATURE ENGINEERING")
    print("================================")

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    access_df = pd.read_csv(ACCESS_LOG_PATH)

    ground_truth_df = pd.read_csv(GROUND_TRUTH_PATH)

    print(f"Access records loaded: {len(access_df)}")
    print(f"Ground-truth records loaded: {len(ground_truth_df)}")

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if len(access_df) != len(ground_truth_df):
        raise ValueError(
            "Access logs and ground truth must contain "
            "the same number of rows."
        )

    # --------------------------------------------------------
    # CREATE EVENT INDEX
    # --------------------------------------------------------

    access_df = access_df.copy()

    access_df["event_index"] = range(
        1,
        len(access_df) + 1
    )

    # --------------------------------------------------------
    # MERGE GROUND TRUTH
    # --------------------------------------------------------

    df = access_df.merge(
        ground_truth_df[
            [
                "event_index",
                "is_anomaly",
                "anomaly_type",
            ]
        ],
        on="event_index",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # VALIDATE GROUND TRUTH
    # --------------------------------------------------------

    if df["is_anomaly"].isna().any():
        raise ValueError(
            "Some access-log records do not have ground truth."
        )

    print("\n================================")
    print("      GROUND TRUTH CHECK")
    print("================================")

    print(
        df["is_anomaly"].value_counts()
        .sort_index()
    )

    # --------------------------------------------------------
    # TIMESTAMP FEATURES
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise"
    )

    df["hour"] = df["timestamp"].dt.hour

    df["day_of_week"] = (
        df["timestamp"].dt.dayofweek
    )

    df["is_unusual_time"] = (
        (df["hour"] < 6)
        | (df["hour"] >= 22)
    ).astype(int)

    # --------------------------------------------------------
    # ACTION FEATURES
    # --------------------------------------------------------

    action = df["action"].astype(str).str.upper()

    df["is_export"] = (
        action == "EXPORT"
    ).astype(int)

    df["is_update"] = (
        action == "UPDATE"
    ).astype(int)

    # --------------------------------------------------------
    # ACCESS RESULT
    # --------------------------------------------------------

    df["is_failed"] = (
        df["success"] == False
    ).astype(int)

    # --------------------------------------------------------
    # USER BEHAVIOUR FEATURES
    #
    # IMPORTANT:
    # These are calculated from the complete normal behaviour
    # distribution, not from the anomaly labels.
    # --------------------------------------------------------

    normal_df = df[
        df["is_anomaly"] == 0
    ].copy()

    user_stats = (
        normal_df
        .groupby("user_id")
        .agg(
            user_avg_records=(
                "records_accessed",
                "mean",
            ),
            user_max_records=(
                "records_accessed",
                "max",
            ),
            user_access_count=(
                "user_id",
                "count",
            ),
            user_failed_count=(
                "is_failed",
                "sum",
            ),
        )
        .reset_index()
    )

    df = df.merge(
        user_stats,
        on="user_id",
        how="left",
    )

    # --------------------------------------------------------
    # HANDLE USERS WITH NO NORMAL HISTORY
    # --------------------------------------------------------

    global_avg_records = normal_df[
        "records_accessed"
    ].mean()

    global_max_records = normal_df[
        "records_accessed"
    ].max()

    global_access_count = (
        normal_df["user_id"].value_counts().mean()
    )

    df["user_avg_records"] = (
        df["user_avg_records"]
        .fillna(global_avg_records)
    )

    df["user_max_records"] = (
        df["user_max_records"]
        .fillna(global_max_records)
    )

    df["user_access_count"] = (
        df["user_access_count"]
        .fillna(global_access_count)
    )

    df["user_failed_count"] = (
        df["user_failed_count"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # RELATIVE ACCESS FEATURE
    # --------------------------------------------------------

    df["records_vs_user_average"] = (
        df["records_accessed"]
        /
        df["user_avg_records"].replace(0, 1)
    )

    # --------------------------------------------------------
    # BULK ACCESS FEATURE
    # --------------------------------------------------------

    df["is_bulk_access"] = (
        df["records_vs_user_average"] >= 5
    ).astype(int)

    # --------------------------------------------------------
    # VERIFY FEATURES
    # --------------------------------------------------------

    missing_features = [
        feature
        for feature in FEATURES
        if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing model features: {missing_features}"
        )

    # --------------------------------------------------------
    # STRATIFIED TRAIN / TEST SPLIT
    #
    # This is critical because anomalies exist only in the
    # final 1,000 rows of the original dataset.
    # --------------------------------------------------------

    train_df, test_df = train_test_split(
        df,
        test_size=0.20,
        random_state=42,
        stratify=df["is_anomaly"],
    )

    # Reset indexes after split
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # --------------------------------------------------------
    # FEATURE VALIDATION
    # --------------------------------------------------------

    print("\n================================")
    print("✓ FEATURE VALIDATION PASSED")
    print("================================")

    print(f"\nModel features: {len(FEATURES)}")

    print("\nFeatures:")

    for feature in FEATURES:
        print(f"  ✓ {feature}")

    # --------------------------------------------------------
    # DATASET DISTRIBUTION
    # --------------------------------------------------------

    print("\n================================")
    print("       DATASET SUMMARY")
    print("================================")

    print("\nTraining distribution:")

    print(
        train_df["is_anomaly"]
        .value_counts()
        .sort_index()
    )

    print("\nTesting distribution:")

    print(
        test_df["is_anomaly"]
        .value_counts()
        .sort_index()
    )

    # --------------------------------------------------------
    # SAVE DATA
    # --------------------------------------------------------

    TRAIN_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    train_df.to_csv(
        TRAIN_OUTPUT_PATH,
        index=False
    )

    test_df.to_csv(
        TEST_OUTPUT_PATH,
        index=False
    )

    print("\nTraining data saved to:")
    print(TRAIN_OUTPUT_PATH)

    print("\nTesting data saved to:")
    print(TEST_OUTPUT_PATH)

    print("\nFeature columns:")
    print(FEATURES)

    return train_df, test_df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    create_features()