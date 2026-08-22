"""Occupancy model — classifies a trip's load as LOW / MEDIUM / HIGH.

The original script here only explored the 108-row occupancy file (one day,
all peak-hour), which is far too thin to train on. We keep that exploration
(headless) for reference, then train a Random Forest CLASSIFIER on the rich
5000-row demand dataset so the model can respond to Day and Weather — which is
what lets the dashboard's occupancy panel stay in sync with the chosen context.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTIFACTS = ROOT / "backend" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# Same feature contract as the demand model (Peak_Hour dropped — constant).
CATEGORICAL = ["Route_ID", "Stop_ID", "Day", "Weather"]
NUMERICAL = ["Bus_Capacity"]
FEATURES = CATEGORICAL + NUMERICAL
TARGET = "Occupancy_Category"
CLASS_ORDER = ["LOW", "MEDIUM", "HIGH"]


def explore_reference_file():
    """Original EDA on the small occupancy file (kept, made headless)."""
    df = pd.read_excel(HERE / "occupancy_synthetic_dataset_routes_1_to_127.xlsx")
    print(df.head())
    print(df.shape)
    print(list(df.columns))
    print("\nMissing values:\n", df.isnull().sum())
    print("\nOccupancy_Category counts:\n", df["Occupancy_Category"].value_counts())

    ax = df["Occupancy_Category"].value_counts().plot(kind="bar")
    ax.set_xlabel("Occupancy Category")
    ax.set_ylabel("Number of Records")
    ax.set_title("Occupancy Category Distribution (reference file)")
    plt.tight_layout()
    plt.savefig(HERE / "occupancy_distribution.png", dpi=120)
    plt.close()


def main():
    explore_reference_file()

    # Train on the larger demand dataset (has day/weather variety).
    df = pd.read_excel(ROOT / "demand_model" / "AI_Fleet_Demand_Dataset_5000.xlsx")
    df["Route_ID"] = df["Route_ID"].astype(int)
    df[TARGET] = df[TARGET].astype(str).str.strip().str.upper()

    X = df[FEATURES]
    y = df[TARGET]
    print("\nTraining occupancy classifier on", len(df), "rows")
    print("Class balance:\n", y.value_counts())

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("numerical", "passthrough", NUMERICAL),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
    ])
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)

    acc = accuracy_score(y_test, pred)
    report = classification_report(y_test, pred, output_dict=True, zero_division=0)
    print(f"\nOccupancy classifier accuracy: {acc:.4f}")
    print(classification_report(y_test, pred, zero_division=0))

    joblib.dump(clf, ARTIFACTS / "occupancy.joblib")
    (ARTIFACTS / "occupancy_meta.json").write_text(json.dumps({
        "target": TARGET,
        "features": FEATURES,
        "categorical": CATEGORICAL,
        "numerical": NUMERICAL,
        "classes": list(clf.named_steps["model"].classes_),
        "class_order": CLASS_ORDER,
        "trained_rows": int(len(df)),
        "accuracy": float(acc),
        "report": report,
    }, indent=2))
    print(f"\nSaved occupancy.joblib, occupancy_meta.json -> {ARTIFACTS}")


if __name__ == "__main__":
    main()
