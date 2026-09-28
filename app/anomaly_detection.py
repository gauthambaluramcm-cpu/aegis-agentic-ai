from pathlib import Path

import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# ============================================================
# PATH CONFIGURATION
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


# ============================================================
# FEATURES
#
# THIS MUST MATCH feature_engineering.py EXACTLY
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
# LOAD DATA
# ============================================================

print("\n================================")
print("       AEGIS ANOMALY DETECTION")
print("================================")

train_df = pd.read_csv(TRAIN_PATH)

test_df = pd.read_csv(TEST_PATH)

print(f"\nTraining records: {len(train_df)}")
print(f"Testing records : {len(test_df)}")


# ============================================================
# FEATURE VALIDATION
# ============================================================

missing_train = [
    feature
    for feature in FEATURES
    if feature not in train_df.columns
]

missing_test = [
    feature
    for feature in FEATURES
    if feature not in test_df.columns
]

if missing_train:
    raise ValueError(
        f"Missing features in training data: {missing_train}"
    )

if missing_test:
    raise ValueError(
        f"Missing features in testing data: {missing_test}"
    )

print("\n✓ Feature list validated")


# ============================================================
# PREPARE X AND Y
# ============================================================

X_train = train_df[FEATURES].copy()

y_train = train_df["is_anomaly"].astype(int)

X_test = test_df[FEATURES].copy()

y_test = test_df["is_anomaly"].astype(int)


# ============================================================
# MODEL
# ============================================================

pipeline = Pipeline(
    steps=[
        (
            "scaler",
            StandardScaler()
        ),
        (
            "classifier",
            RandomForestClassifier(
                random_state=42,
                class_weight="balanced",
                n_jobs=-1,
            )
        ),
    ]
)


# ============================================================
# HYPERPARAMETER TUNING
# ============================================================

print("\n================================")
print("       PARAMETER TUNING")
print("================================")

param_grid = {
    "classifier__n_estimators": [
        200,
        400,
    ],

    "classifier__max_depth": [
        5,
        6,
        8,
    ],

    "classifier__min_samples_split": [
        5,
        10,
    ],

    "classifier__min_samples_leaf": [
        2,
        5,
    ],

    "classifier__max_features": [
        "sqrt",
        "log2",
    ],
}


grid_search = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    scoring="f1",
    cv=5,
    n_jobs=-1,
    verbose=0,
)


grid_search.fit(
    X_train,
    y_train
)


model = grid_search.best_estimator_


print("\n================================")
print("       BEST PARAMETERS")
print("================================")

print(
    grid_search.best_params_
)

print(
    f"\nBest F1 from tuning: "
    f"{grid_search.best_score_:.4f}"
)


# ============================================================
# PREDICTION PROBABILITIES
# ============================================================

probabilities = model.predict_proba(
    X_test
)[:, 1]


# ============================================================
# DEFAULT THRESHOLD EVALUATION
# ============================================================

default_predictions = (
    probabilities >= 0.50
).astype(int)


precision = precision_score(
    y_test,
    default_predictions,
    zero_division=0,
)

recall = recall_score(
    y_test,
    default_predictions,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    default_predictions,
    zero_division=0,
)

roc_auc = roc_auc_score(
    y_test,
    probabilities,
)

pr_auc = average_precision_score(
    y_test,
    probabilities,
)


print("\n================================")
print("       TUNED RANDOM FOREST")
print("================================")

print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")
print(f"ROC-AUC   : {roc_auc:.4f}")
print(f"PR-AUC    : {pr_auc:.4f}")

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_test,
        default_predictions
    )
)


# ============================================================
# THRESHOLD TUNING
# ============================================================

print("\n================================")
print("       THRESHOLD TUNING")
print("================================")

threshold_results = []

thresholds = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
    0.85,
    0.90,
]


for threshold in thresholds:

    predictions = (
        probabilities >= threshold
    ).astype(int)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    threshold_results.append(
        {
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    )


threshold_df = pd.DataFrame(
    threshold_results
)


print(
    threshold_df.to_string(
        index=False
    )
)


# ============================================================
# BEST THRESHOLD
# ============================================================

best_row = threshold_df.loc[
    threshold_df["f1"].idxmax()
]

best_threshold = float(
    best_row["threshold"]
)

best_precision = float(
    best_row["precision"]
)

best_recall = float(
    best_row["recall"]
)

best_f1 = float(
    best_row["f1"]
)


print("\n================================")
print("       BEST THRESHOLD")
print("================================")

print(
    f"Threshold : {best_threshold:.2f}"
)

print(
    f"Precision : {best_precision:.4f}"
)

print(
    f"Recall    : {best_recall:.4f}"
)

print(
    f"F1 Score  : {best_f1:.4f}"
)


# ============================================================
# FINAL PREDICTIONS
# ============================================================

final_predictions = (
    probabilities >= best_threshold
).astype(int)


# ============================================================
# FINAL DETECTOR
# ============================================================

print("\n================================")
print("       FINAL DETECTOR")
print("================================")

print(
    f"Threshold : {best_threshold:.2f}"
)

print(
    f"Precision : "
    f"{precision_score(y_test, final_predictions, zero_division=0):.4f}"
)

print(
    f"Recall    : "
    f"{recall_score(y_test, final_predictions, zero_division=0):.4f}"
)

print(
    f"F1 Score  : "
    f"{f1_score(y_test, final_predictions, zero_division=0):.4f}"
)

print("\nFinal Confusion Matrix:")

print(
    confusion_matrix(
        y_test,
        final_predictions
    )
)
# ============================================================
# SAVE ML PREDICTIONS
# ============================================================

ml_results = test_df.copy()

ml_results["ml_anomaly"] = final_predictions
ml_results["ml_probability"] = probabilities

ml_output_path = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml_test_results.csv"
)

ml_results.to_csv(
    ml_output_path,
    index=False
)

print("\nML results saved to:")
print(ml_output_path)

# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n================================")
print("       FEATURE IMPORTANCE")
print("================================")

classifier = model.named_steps[
    "classifier"
]

importance_df = pd.DataFrame(
    {
        "feature": FEATURES,
        "importance": classifier.feature_importances_,
    }
).sort_values(
    "importance",
    ascending=False
)


print(
    importance_df.to_string(
        index=False
    )
)


# ============================================================
# ANOMALY TYPE ANALYSIS
# ============================================================

print("\n================================")
print("     ANOMALY TYPE ANALYSIS")
print("================================")

analysis_df = test_df.copy()

analysis_df["predicted_anomaly"] = (
    final_predictions
)

analysis_df["prediction_probability"] = (
    probabilities
)

anomaly_df = analysis_df[
    analysis_df["is_anomaly"] == 1
].copy()


if len(anomaly_df) > 0:

    type_summary = (
        anomaly_df
        .groupby("anomaly_type")
        .agg(
            DETECTED=(
                "predicted_anomaly",
                "sum",
            ),
            TOTAL=(
                "is_anomaly",
                "count",
            ),
        )
    )

    type_summary["MISSED"] = (
        type_summary["TOTAL"]
        -
        type_summary["DETECTED"]
    )

    type_summary["RECALL"] = (
        type_summary["DETECTED"]
        /
        type_summary["TOTAL"]
    )

    type_summary = type_summary[
        [
            "DETECTED",
            "MISSED",
            "TOTAL",
            "RECALL",
        ]
    ]

    print("\n--- DETECTION BY ANOMALY TYPE ---")

    print(
        type_summary.to_string()
    )


# ============================================================
# MISSED ANOMALIES
# ============================================================

missed = analysis_df[
    (analysis_df["is_anomaly"] == 1)
    &
    (analysis_df["predicted_anomaly"] == 0)
].copy()


print("\n================================")
print("       MISSED ANOMALIES")
print("================================")

print(
    f"Total missed: {len(missed)}"
)


if len(missed) > 0:

    print("\n--- MISSED ANOMALY TYPES ---")

    print(
        missed["anomaly_type"]
        .value_counts()
    )

    print("\n--- SAMPLE MISSED ANOMALIES ---")

    columns_to_show = [
        "user_id",
        "timestamp",
        "dataset_name",
        "action",
        "records_accessed",
        "location",
        "device",
        "anomaly_type",
        "prediction_probability",
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in missed.columns
    ]

    print(
        missed[
            available_columns
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

actual_anomalies = int(
    (y_test == 1).sum()
)

detected_anomalies = int(
    ((y_test == 1) & (final_predictions == 1)).sum()
)

missed_anomalies = int(
    ((y_test == 1) & (final_predictions == 0)).sum()
)

false_alarms = int(
    ((y_test == 0) & (final_predictions == 1)).sum()
)

final_f1 = f1_score(
    y_test,
    final_predictions,
    zero_division=0,
)

final_recall = recall_score(
    y_test,
    final_predictions,
    zero_division=0,
)


print("\n================================")
print("        AEGIS SUMMARY")
print("================================")

print(
    f"Actual anomalies : {actual_anomalies}"
)

print(
    f"Detected         : {detected_anomalies}"
)

print(
    f"Missed           : {missed_anomalies}"
)

print(
    f"False alarms     : {false_alarms}"
)

print(
    f"Final F1         : {final_f1:.4f}"
)

print(
    f"Final Recall     : {final_recall:.4f}"
)

print("\n================================")
print("          COMPLETE")
print("================================")