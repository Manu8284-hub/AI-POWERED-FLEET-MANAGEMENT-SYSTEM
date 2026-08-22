"""Bus-stop clustering — groups stops into demand tiers with K-Means.

Keeps the elbow + silhouette workflow, drops the constant `Unique_Routes`
column, labels the three clusters High demand / Balanced / Emerging (A/B/C, to
match the dashboard legend), and adds a PCA(2) projection so each stop gets a
stable (x, y) the UI can plot. Everything the API serves is precomputed here
into clusters.json.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pandas as pd
import joblib

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTIFACTS = ROOT / "backend" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# Drop `Unique_Routes` (constant = 1). Max_Passenger_Count adds peak signal.
FEATURES = [
    "Avg_Passenger_Count",
    "Avg_Occupancy_Percentage",
    "Avg_Delay_Minutes",
    "Peak_Hour_Trips",
    "Max_Passenger_Count",
]
N_CLUSTERS = 3
# Rank clusters by average demand, then label highest -> lowest.
RANKED_LABELS = [
    {"letter": "A", "name": "High demand"},
    {"letter": "B", "name": "Balanced"},
    {"letter": "C", "name": "Emerging"},
]


def main():
    df = pd.read_excel(HERE / "Bus_Stop_Clustering_Dataset.xlsx")
    print(df.head())
    print(df.shape)
    print(list(df.columns))
    print("\nMissing values:\n", df.isnull().sum())

    X = df[FEATURES]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Elbow curve (saved)
    inertia = []
    for k in range(2, 8):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X_scaled)
        inertia.append(km.inertia_)
    plt.figure()
    plt.plot(range(2, 8), inertia, marker="o")
    plt.xlabel("Number of Clusters")
    plt.ylabel("Inertia")
    plt.title("Elbow Method")
    plt.tight_layout()
    plt.savefig(HERE / "elbow.png", dpi=120)
    plt.close()

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df["Cluster"] = kmeans.fit_predict(X_scaled)

    score = float(silhouette_score(X_scaled, df["Cluster"]))
    print("\nSilhouette Score:", round(score, 4))
    print("Cluster distribution:\n", df["Cluster"].value_counts())

    # Rank raw cluster ids by mean passenger count -> stable A/B/C labels.
    order = (
        df.groupby("Cluster")["Avg_Passenger_Count"].mean()
        .sort_values(ascending=False).index.tolist()
    )
    label_map = {int(cid): RANKED_LABELS[i] for i, cid in enumerate(order)}

    # PCA(2) -> normalise to 0..100 so the UI can position stops directly.
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)

    def norm(col):
        lo, hi = col.min(), col.max()
        return (col - lo) / (hi - lo) * 100 if hi > lo else col * 0 + 50

    xs = norm(coords[:, 0])
    ys = norm(coords[:, 1])

    stops = []
    for i, row in df.reset_index(drop=True).iterrows():
        lab = label_map[int(row["Cluster"])]
        stops.append({
            "stop_id": str(row["Stop_ID"]),
            "stop_name": str(row["Stop_Name"]),
            "cluster": int(row["Cluster"]),
            "label": lab["letter"],
            "label_name": lab["name"],
            "x": round(float(xs[i]), 2),
            "y": round(float(ys[i]), 2),
            "avg_passengers": round(float(row["Avg_Passenger_Count"]), 2),
            "avg_occupancy": round(float(row["Avg_Occupancy_Percentage"]), 2),
        })

    summary = []
    for cid in order:
        grp = df[df["Cluster"] == cid]
        lab = label_map[int(cid)]
        summary.append({
            "cluster": int(cid),
            "label": lab["letter"],
            "label_name": lab["name"],
            "count": int(len(grp)),
            "avg_passengers": round(float(grp["Avg_Passenger_Count"].mean()), 2),
            "avg_occupancy": round(float(grp["Avg_Occupancy_Percentage"].mean()), 2),
            "avg_delay": round(float(grp["Avg_Delay_Minutes"].mean()), 2),
        })
    print("\nCluster summary:")
    for s in summary:
        print(f"  {s['label']} ({s['label_name']}): {s['count']} stops, "
              f"avg {s['avg_passengers']} pax, {s['avg_occupancy']}% occ")

    # Scatter (saved)
    plt.figure()
    plt.scatter(df["Avg_Passenger_Count"], df["Avg_Occupancy_Percentage"], c=df["Cluster"])
    plt.xlabel("Average Passenger Count")
    plt.ylabel("Average Occupancy Percentage")
    plt.title("Bus Stop Clusters")
    plt.tight_layout()
    plt.savefig(HERE / "clusters.png", dpi=120)
    plt.close()

    joblib.dump(
        {"scaler": scaler, "kmeans": kmeans, "pca": pca,
         "features": FEATURES, "label_map": label_map},
        ARTIFACTS / "clusters.joblib",
    )
    (ARTIFACTS / "clusters.json").write_text(json.dumps({
        "features": FEATURES,
        "n_clusters": N_CLUSTERS,
        "silhouette": score,
        "summary": summary,
        "stops": stops,
    }, indent=2))
    print(f"\nSaved clusters.joblib, clusters.json -> {ARTIFACTS}")


if __name__ == "__main__":
    main()
