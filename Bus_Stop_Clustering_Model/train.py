"""
Bus Stop Clustering Model

Clusters bus stops based on passenger demand, occupancy,
delay, peak-hour activity, and route usage.

The model uses the single master dataset:

    fleet_master_combined_dataset.xlsx

The master dataset contains multiple records for each stop,
so we keep only one record per Stop_ID before clustering.
"""

import json
from pathlib import Path

import pandas as pd
import joblib

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

ARTIFACTS = ROOT / "backend" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Clustering features
# ---------------------------------------------------------

FEATURES = [
    "Avg_Passenger_Count",
    "Avg_Occupancy_Percentage",
    "Avg_Delay_Minutes",
    "Peak_Hour_Trips",
    "Max_Passenger_Count"
]


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    # -----------------------------------------------------
    # Load master dataset
    # -----------------------------------------------------

    dataset_path = ROOT / "fleet_master_combined_dataset.xlsx"

    print("=" * 70)
    print("Loading master fleet dataset")
    print("=" * 70)

    print(f"\nDataset: {dataset_path}")

    df = pd.read_excel(dataset_path)

    print(f"\nOriginal dataset shape: {df.shape}")
    print(f"Original rows: {len(df)}")


    # -----------------------------------------------------
    # Keep one row per bus stop
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=["Stop_ID"]
    ).copy()

    print("\nAfter keeping one record per Stop_ID:")
    print(f"Rows: {len(df)}")
    print(f"Unique stops: {df['Stop_ID'].nunique()}")


    # -----------------------------------------------------
    # Check required columns
    # -----------------------------------------------------

    required_columns = [
        "Stop_ID"
    ] + FEATURES

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


    # -----------------------------------------------------
    # Remove missing values
    # -----------------------------------------------------

    df = df.dropna(
        subset=FEATURES
    ).copy()

    print(
        f"\nRows after removing missing values: {len(df)}"
    )


    # -----------------------------------------------------
    # Prepare feature matrix
    # -----------------------------------------------------

    X = df[FEATURES].copy()

    print("\nClustering features:")

    for feature in FEATURES:
        print(f"  - {feature}")


    # -----------------------------------------------------
    # Scale features
    # -----------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)


    # -----------------------------------------------------
    # Find suitable number of clusters
    # -----------------------------------------------------

    best_k = 2
    best_score = -1

    max_k = min(6, len(df) - 1)

    print("\n" + "=" * 70)
    print("Testing different cluster counts")
    print("=" * 70)

    for k in range(2, max_k + 1):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(
            X_scaled
        )

        score = silhouette_score(
            X_scaled,
            labels
        )

        print(
            f"K = {k}  |  Silhouette Score = {score:.4f}"
        )

        if score > best_score:
            best_score = score
            best_k = k


    print("\nBest number of clusters:", best_k)
    print(
        f"Best silhouette score: {best_score:.4f}"
    )


    # -----------------------------------------------------
    # Train final KMeans model
    # -----------------------------------------------------

    print("\nTraining final clustering model...")

    kmeans = KMeans(
        n_clusters=best_k,
        random_state=42,
        n_init=10
    )

    df["Cluster"] = kmeans.fit_predict(
        X_scaled
    )


    # -----------------------------------------------------
    # Display cluster distribution
    # -----------------------------------------------------

    print("\nCluster distribution:")

    print(
        df["Cluster"]
        .value_counts()
        .sort_index()
    )


    # -----------------------------------------------------
    # Save clustering model
    # -----------------------------------------------------

    model_path = ARTIFACTS / "clustering.joblib"

    joblib.dump(
        {
            "model": kmeans,
            "scaler": scaler,
            "features": FEATURES
        },
        model_path
    )


    # -----------------------------------------------------
    # Save cluster results
    # -----------------------------------------------------

    results = df[
        ["Stop_ID"] + FEATURES + ["Cluster"]
    ].copy()

    results_path = (
        ARTIFACTS /
        "cluster_results.csv"
    )

    results.to_csv(
        results_path,
        index=False
    )


    # -----------------------------------------------------
    # Save metadata
    # -----------------------------------------------------

    metadata = {
        "features": FEATURES,
        "n_clusters": int(best_k),
        "silhouette_score": float(best_score),
        "trained_stops": int(len(df)),
        "clusters": sorted(
            df["Cluster"]
            .unique()
            .tolist()
        )
    }

    metadata_path = (
        ARTIFACTS /
        "clustering_meta.json"
    )

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
    print("Bus Stop Clustering completed successfully!")
    print("=" * 70)

    print("\nSaved model:")
    print(model_path)

    print("\nSaved cluster results:")
    print(results_path)

    print("\nSaved metadata:")
    print(metadata_path)


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    main()