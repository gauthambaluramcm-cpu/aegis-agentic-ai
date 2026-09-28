from pathlib import Path

import pandas as pd


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

FEATURE_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "access_features.csv"
)

GROUND_TRUTH_PATH = (
    BASE_DIR
    / "data"
    / "ground_truth"
    / "anomaly_ground_truth.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml_dataset.csv"
)


# --------------------------------------------------
# CREATE ML DATASET
# --------------------------------------------------

def create_ml_dataset():

    print("\n================================")
    print("      AEGIS ML DATASET")
    print("================================")

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------

    features = pd.read_csv(FEATURE_PATH)
    ground_truth = pd.read_csv(GROUND_TRUTH_PATH)

    print(f"Feature records: {len(features)}")
    print(f"Ground-truth records: {len(ground_truth)}")

    # --------------------------------------------------
    # VALIDATE ROW ALIGNMENT
    # --------------------------------------------------

    if len(features) != len(ground_truth):
        raise ValueError(
            "Feature and ground-truth datasets "
            "have different numbers of rows."
        )

    expected_indexes = range(1, len(ground_truth) + 1)

    actual_indexes = ground_truth["event_index"].tolist()

    if actual_indexes != list(expected_indexes):
        raise ValueError(
            "Ground-truth event_index is not sequential. "
            "Cannot safely align labels by row order."
        )

    print("✓ Row counts match")
    print("✓ Ground-truth event indexes validated")

    # --------------------------------------------------
    # ATTACH GROUND-TRUTH LABELS
    # --------------------------------------------------

    features["is_anomaly"] = (
        ground_truth["is_anomaly"].values
    )

    features["anomaly_type"] = (
        ground_truth["anomaly_type"].values
    )

    # --------------------------------------------------
    # VALIDATE LABELS
    # --------------------------------------------------

    print("\n--- LABEL DISTRIBUTION ---")

    print(
        features["is_anomaly"]
        .value_counts()
        .sort_index()
    )

    print("\n--- ANOMALY TYPES ---")

    print(
        features["anomaly_type"]
        .value_counts()
    )

    # --------------------------------------------------
    # SAVE DATASET
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    features.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"\n✓ ML dataset saved to:\n{OUTPUT_PATH}"
    )

    print(
        f"\nTotal ML records: {len(features)}"
    )

    print(
        f"Total features: {len(features.columns)}"
    )

    return features


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    create_ml_dataset()