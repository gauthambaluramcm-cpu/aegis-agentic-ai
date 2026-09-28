from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "ml_dataset.csv"

TRAIN_FILE = BASE_DIR / "data" / "processed" / "train.csv"
TEST_FILE = BASE_DIR / "data" / "processed" / "test.csv"


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("\n================================")
    print("     AEGIS TRAIN-TEST SPLIT")
    print("================================")

    # Load ML dataset
    df = pd.read_csv(INPUT_FILE)

    print(f"Total records: {len(df)}")

    # --------------------------------------------------
    # SEPARATE FEATURES AND TARGET
    # --------------------------------------------------

    X = df.drop(columns=["is_anomaly"])
    y = df["is_anomaly"]

    # --------------------------------------------------
    # STRATIFIED 80/20 SPLIT
    # --------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # --------------------------------------------------
    # REBUILD TRAINING AND TEST DATASETS
    # --------------------------------------------------

    train_df = X_train.copy()
    train_df["is_anomaly"] = y_train

    test_df = X_test.copy()
    test_df["is_anomaly"] = y_test

    # Reset indexes
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # --------------------------------------------------
    # SAVE DATASETS
    # --------------------------------------------------

    train_df.to_csv(TRAIN_FILE, index=False)
    test_df.to_csv(TEST_FILE, index=False)

    # --------------------------------------------------
    # DISPLAY DISTRIBUTION
    # --------------------------------------------------

    print("\n--- TRAINING DATA ---")
    print(f"Records: {len(train_df)}")
    print(train_df["is_anomaly"].value_counts())
    print(
        "Anomaly percentage:",
        round(train_df["is_anomaly"].mean() * 100, 2),
        "%"
    )

    print("\n--- TEST DATA ---")
    print(f"Records: {len(test_df)}")
    print(test_df["is_anomaly"].value_counts())
    print(
        "Anomaly percentage:",
        round(test_df["is_anomaly"].mean() * 100, 2),
        "%"
    )

    print("\n================================")
    print("✓ TRAIN-TEST SPLIT COMPLETED")
    print("================================")

    print(f"\nTraining data saved to:")
    print(TRAIN_FILE)

    print(f"\nTest data saved to:")
    print(TEST_FILE)


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()