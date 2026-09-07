"""Demand model — predicts Passenger_Count for a trip.

Trains Linear Regression vs Random Forest, keeps the comparison the project
started with, then PERSISTS the Random Forest pipeline (the winner) plus its
metrics and a per-route defaults table so the API can predict from just a
route id. Runs headless (matplotlib Agg) so it is safe in `npm run train`.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless: save figures instead of blocking on show()
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTIFACTS = ROOT / "backend" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# Feature contract (shared with the API). Peak_Hour is dropped: it is a
# constant (=1) across the whole dataset, so it carries zero signal.
CATEGORICAL = ["Route_ID", "Stop_ID", "Day", "Weather"]
NUMERICAL = ["Bus_Capacity"]
FEATURES = CATEGORICAL + NUMERICAL
TARGET = "Passenger_Count"


def main():
    # Step 1: Load dataset
    df = pd.read_excel(ROOT / "fleet_master_combined_dataset.xlsx")
    print(df.head())
    print(df.shape)
    print(list(df.columns))

    # Step 2/3: Basic data health checks
    print("\nMissing values:\n", df.isnull().sum())
    print("\nData types:\n", df.dtypes)

    df["Route_ID"] = df["Route_ID"].astype(int)
    X = df[FEATURES]
    y = df[TARGET]

    # Step 6: Encode categoricals, pass the numeric column through untouched.
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("numerical", "passthrough", NUMERICAL),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print("\nTraining data:", X_train.shape, "| Testing data:", X_test.shape)

    def evaluate(name, model):
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        r2 = r2_score(y_test, pred)
        print(f"\n{name} Results\nMAE: {mae:.3f}\nRMSE: {rmse:.3f}\nR2 Score: {r2:.4f}")
        return {"mae": float(mae), "rmse": rmse, "r2": float(r2)}, pred

    # MODEL 1: Linear Regression
    linear_model = Pipeline([("preprocessor", preprocessor), ("model", LinearRegression())])
    linear_metrics, _ = evaluate("Linear Regression", linear_model)

    # MODEL 2: Random Forest (persisted as the production model)
    random_forest_model = Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
    ])
    rf_metrics, rf_pred = evaluate("Random Forest", random_forest_model)

    print("\nModel Comparison")
    print(pd.DataFrame({
        "Model": ["Linear Regression", "Random Forest"],
        "MAE": [linear_metrics["mae"], rf_metrics["mae"]],
        "RMSE": [linear_metrics["rmse"], rf_metrics["rmse"]],
        "R2 Score": [linear_metrics["r2"], rf_metrics["r2"]],
    }))

    # Actual vs Predicted (saved, not shown)
    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, rf_pred, s=8, alpha=0.4)
    lims = [min(y_test.min(), rf_pred.min()), max(y_test.max(), rf_pred.max())]
    plt.plot(lims, lims, "r--", linewidth=1)
    plt.xlabel("Actual Passenger Count")
    plt.ylabel("Predicted Passenger Count")
    plt.title("Actual vs Predicted Passenger Demand (Random Forest)")
    plt.tight_layout()
    plt.savefig(HERE / "actual_vs_predicted.png", dpi=120)
    plt.close()

    # Per-route defaults: lets the API build a full feature row from a route id
    # alone (most-common stop, typical capacity for that route).
    route_defaults = {}
    for rid, grp in df.groupby("Route_ID"):
        route_defaults[str(int(rid))] = {
            "stop_id": str(grp["Stop_ID"].mode().iat[0]),
            "stop_name": str(grp["Stop_Name"].mode().iat[0]),
            "capacity": int(grp["Bus_Capacity"].median()),
        }
    default_capacity = int(df["Bus_Capacity"].median())

    # Persist artifacts
    joblib.dump(random_forest_model, ARTIFACTS / "demand.joblib")
    (ARTIFACTS / "demand_meta.json").write_text(json.dumps({
        "target": TARGET,
        "features": FEATURES,
        "categorical": CATEGORICAL,
        "numerical": NUMERICAL,
        "trained_rows": int(len(df)),
        "linear": linear_metrics,
        "random_forest": rf_metrics,
        "default_capacity": default_capacity,
    }, indent=2))
    (ARTIFACTS / "route_defaults.json").write_text(json.dumps({
        "default_capacity": default_capacity,
        "routes": route_defaults,
    }, indent=2))

    print(f"\nSaved demand.joblib, demand_meta.json, route_defaults.json -> {ARTIFACTS}")
    print(f"Routes with training data: {len(route_defaults)} (of 127 published)")

    # Example prediction (sanity check)
    sample = pd.DataFrame([{ "Route_ID": 1, "Stop_ID": "R1_S01", "Day": "Monday",
                             "Weather": "Clear", "Bus_Capacity": 50 }])
    print("Example predicted demand (R01, Monday, Clear):",
          round(float(random_forest_model.predict(sample)[0]), 2))


if __name__ == "__main__":
    main()
