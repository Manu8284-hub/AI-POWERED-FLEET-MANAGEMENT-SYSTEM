"""
Occupancy Model

Classifies a trip's load as LOW / MEDIUM / HIGH.

This model uses the single master dataset:
    fleet_master_combined_dataset.xlsx

The model predicts Occupancy_Category using route, stop, day,
weather, and bus capacity information.
"""

import json
from pathlib import Path

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

ARTIFACTS = ROOT / "backend" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Features
# ---------------------------------------------------------

CATEGORICAL = [
    "Route_ID",
    "Stop_ID",
    "Day",
    "Weather"
]

NUMERICAL = [
    "Bus_Capacity"
]

FEATURES = CATEGORICAL + NUMERICAL

TARGET = "Occupancy_Category"

CLASS_ORDER = [
    "LOW",
    "MEDIUM",
    "HIGH"
]


# ---------------------------------------------------------
# Main training function
# ---------------------------------------------------------

def main():

    # -----------------------------------------------------
    # Load the single master dataset
    # -----------------------------------------------------

    dataset_path = ROOT / "fleet_master_combined_dataset.xlsx"

    print("=" * 70)
    print("Loading master fleet dataset")
    print("=" * 70)
    print(f"Dataset: {dataset_path}")

    df = pd.read_excel(dataset_path)

    print(f"\nDataset shape: {df.shape}")
    print(f"Rows: {len(df)}")


    # -----------------------------------------------------
    # Basic data preparation
    # -----------------------------------------------------

    df["Route_ID"] = df["Route_ID"].astype(str).str.strip()
    df["Stop_ID"] = df["Stop_ID"].astype(str).str.strip()

    df["Day"] = df["Day"].astype(str).str.strip()
    df["Weather"] = df["Weather"].astype(str).str.strip()

    df[TARGET] = (
        df[TARGET]
        .astype(str)
        .str.strip()
        .str.upper()
    )


    # -----------------------------------------------------
    # Check required columns
    # -----------------------------------------------------

    required_columns = FEATURES + [TARGET]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


    # -----------------------------------------------------
    # Remove rows with missing required values
    # -----------------------------------------------------

    df = df.dropna(subset=required_columns).copy()

    print(f"Rows after cleaning: {len(df)}")


    # -----------------------------------------------------
    # Features and target
    # -----------------------------------------------------

    X = df[FEATURES]
    y = df[TARGET]

    print("\nFeatures:")
    print(FEATURES)

    print("\nTarget:")
    print(TARGET)

    print("\nClass balance:")
    print(y.value_counts())


    # -----------------------------------------------------
    # Preprocessing
    # -----------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                CATEGORICAL
            ),
            (
                "numerical",
                "passthrough",
                NUMERICAL
            )
        ]
    )


    # -----------------------------------------------------
    # Train / Test split
    # -----------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("\nTraining rows:", len(X_train))
    print("Testing rows:", len(X_test))


    # -----------------------------------------------------
    # Random Forest Classifier
    # -----------------------------------------------------

    clf = Pipeline([
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
        )
    ])


    # -----------------------------------------------------
    # Train model
    # -----------------------------------------------------

    print("\nTraining occupancy classifier...")

    clf.fit(X_train, y_train)


    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    pred = clf.predict(X_test)


    # -----------------------------------------------------
    # Evaluation
    # -----------------------------------------------------

    acc = accuracy_score(y_test, pred)

    report = classification_report(
        y_test,
        pred,
        output_dict=True,
        zero_division=0
    )

    print("\n" + "=" * 70)
    print("OCCUPANCY MODEL RESULTS")
    print("=" * 70)

    print(f"\nAccuracy: {acc:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            pred,
            zero_division=0
        )
    )


    # -----------------------------------------------------
    # Save trained model
    # -----------------------------------------------------

    model_path = ARTIFACTS / "occupancy.joblib"

    joblib.dump(
        clf,
        model_path
    )


    # -----------------------------------------------------
    # Save model metadata
    # -----------------------------------------------------

    metadata = {
        "target": TARGET,
        "features": FEATURES,
        "categorical": CATEGORICAL,
        "numerical": NUMERICAL,
        "classes": list(
            clf.named_steps["model"].classes_
        ),
        "class_order": CLASS_ORDER,
        "trained_rows": int(len(df)),
        "accuracy": float(acc),
        "report": report
    }

    metadata_path = ARTIFACTS / "occupancy_meta.json"

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2
        )
    )


    # -----------------------------------------------------
    # Done
    # -----------------------------------------------------

    print("\n" + "=" * 70)
    print("Occupancy model training completed successfully!")
    print("=" * 70)

    print(f"\nSaved model:")
    print(model_path)

    print("\nSaved metadata:")
    print(metadata_path)


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    main()