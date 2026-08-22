# FleetIQ — AI-Powered Fleet Optimisation Platform

FleetIQ is a full-stack college bus fleet dashboard. Three scikit-learn models
(demand regression, occupancy classification, stop clustering) are trained and
persisted, served by a FastAPI backend, and consumed by a React 19 + Vite
dashboard that updates **live** and stays **in sync** across every panel.

> Every metric on the dashboard is now a **real model prediction** — no synthetic
> constants. The one honest caveat is the live feed (see [Is it really real-time?](#is-it-really-real-time)).

## Architecture

```
 xlsx datasets ─►  */train.py            ─►  backend/artifacts/*.joblib + *.json
 (fixed data)      (train + persist)          (models + metadata + route defaults)
                                                        │
                                          backend/app.py  (FastAPI)
                                          backend/ml.py   (load once, predict, aggregate)
                                                        │  Vite proxy  /api → :8000
                                          src/App.jsx     (fetch + EventSource/SSE)
```

- **`demand_model/`**, **`occupancy_model/`**, **`Bus_Stop_Clustering_Model/`** — one
  `train.py` per model. Each keeps its console EDA, writes its figure to a `.png`,
  and dumps a model + metadata into `backend/artifacts/`.
- **`backend/train.py`** — thin runner that trains all three in sequence.
- **`backend/ml.py`** — loads the artifacts once and does all prediction/aggregation.
- **`backend/app.py`** — FastAPI app exposing everything under `/api`, including the
  `/api/stream` Server-Sent Events feed.
- **`src/`** — `api.js` (fetch helpers), `hooks.js` (data + live-stream hooks),
  `App.jsx` (dashboard). Vite proxies `/api` to the backend so there is no CORS in dev.

## Models (trained, not synthetic)

| Model | Algorithm | Data | Headline metric |
|---|---|---|---|
| **Demand** | `RandomForestRegressor` in a One-Hot `Pipeline` | 5,000 rows | R² **0.923**, MAE **±3.2** passengers |
| **Occupancy** | `RandomForestClassifier` (LOW / MEDIUM / HIGH) | 5,000 rows | accuracy **84.9%** on a 1,000-row holdout |
| **Clusters** | `StandardScaler` + `KMeans(k=3)` + PCA(2) for map coords | 108 stops | silhouette **0.347**; A High-demand (55), B Balanced (15), C Emerging (38) |

Notes:
- The demand trainer also fits a `LinearRegression` baseline (R² ≈ 0.940) for comparison
  and prints both; the **Random Forest is persisted** for its robustness to unseen
  routes and non-linear day/weather interactions.
- Occupancy is trained on the richer 5,000-row demand dataset (the 108-row occupancy
  file is Wednesday-only — too thin to learn from; its EDA is kept for reference).
- Two dead constant columns (`Peak_Hour`, `Unique_Routes`) are dropped during training.
- Only 108 of the 127 published routes appear in the training data. The One-Hot encoder
  uses `handle_unknown="ignore"`, so the API degrades gracefully for unseen routes
  instead of erroring.

## Quick start

Prerequisites: **Python 3.10+** and **Node 20.19+ / 22.12+**.

```bash
# 1. install both toolchains
pip install -r requirements.txt
npm install

# 2. train + persist the models (fills backend/artifacts/)
npm run train

# 3. run the backend API and the dashboard together
npm run dev:all
```

`npm run dev:all` uses [`concurrently`](https://www.npmjs.com/package/concurrently)
to start the FastAPI server (`:8000`) and the Vite dev server together. Open the URL
Vite prints (normally `http://localhost:5173`). The dashboard talks to the API through
the Vite `/api` proxy, so both run same-origin with no CORS setup.

Individual commands, if you prefer separate terminals:

```bash
npm run train   # python backend/train.py
npm run api     # uvicorn backend.app:app --reload --port 8000
npm run dev     # vite
```

## Using the dashboard

- **Day + Weather** selectors in the top bar are the global context. Changing either
  re-fetches and updates **every** panel at once (stat cards, demand chart, occupancy
  donut, recommendations, and the selected route's prediction) — this is the "sync".
- **Stat cards** show the network total predicted riders, high-occupancy-risk route
  count, and fleet efficiency. The rider / risk / efficiency figures **tick live** from
  the SSE stream; the sidebar dot is green while the feed is connected.
- **Demand forecast** draws a 7-day predicted curve vs. fleet capacity for the chosen
  weather (the SVG is built from the model output, with a dynamic y-axis).
- **Occupancy** shows the LOW/MEDIUM/HIGH distribution and average load for the chosen day.
- **Stop clusters** plots all 108 stops at their PCA coordinates, coloured by cluster.
- **Recommendations** are derived by comparing predicted demand vs. capacity per route.
  **Run fleet optimisation** (hero button) recomputes them and shows a toast.
- **Route schedule** panel: pick a route to see the official 2026-27 schedule page **and**
  that route's live ML prediction (predicted riders, load %, occupancy risk).

## Is it really real-time?

The datasets are fixed files, so there is **no live GPS/sensor feed** in this project.
The `/api/stream` SSE endpoint is **simulated live telemetry over real predictions**:
every ~3 seconds it takes the genuine model baseline for the current day/weather and
applies a small time-wave + noise, so the numbers move like a live operations board
while remaining anchored to real model output. This is labelled honestly in the code
(`backend/app.py`) and in the UI ("Live · every 3s"). Everything else — the forecasts,
occupancy classes, clusters, and recommendations — is a direct model prediction with no
fluctuation added.

## API reference

All endpoints are under `/api` (proxied to `:8000` in dev).

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/api/health` | model-loaded status |
| GET | `/api/context` | day/weather options, route list, model metrics |
| GET | `/api/overview?day=&weather=` | stat cards + occupancy distribution + peak day |
| GET | `/api/demand/forecast?weather=&route=` | 7-day predicted series + capacity line |
| POST | `/api/predict/demand` | `{route,day,weather,capacity?}` → predicted passengers |
| POST | `/api/predict/occupancy` | → category + class probabilities |
| GET | `/api/clusters` | per-stop `{label,x,y,...}` + cluster summary |
| GET | `/api/recommendations?day=&weather=` | fleet actions (overload/idle/combine) |
| POST | `/api/optimise?day=&weather=` | recomputed priority actions (hero button) |
| GET | `/api/stream?day=&weather=` | SSE: `{riders, high_risk, efficiency, active_buses}` every ~3s |

## Project structure

```text
backend/
  app.py              FastAPI app + SSE stream
  ml.py               loads artifacts, prediction + aggregation helpers
  train.py            runs all three trainers in sequence
  artifacts/          persisted models + metadata (git-ignored; run `npm run train`)
demand_model/train.py            RandomForest demand regressor
occupancy_model/train.py         RandomForest occupancy classifier
Bus_Stop_Clustering_Model/train.py   KMeans stop clustering
src/
  App.jsx             dashboard UI (consumes the API)
  api.js              fetch/post/stream helpers
  hooks.js            useApiContext / useDashboard / useClusters / useLiveStream
  data/routes.js      official 127-route schedule metadata
  main.jsx            React entry point
public/Bus-Routes-2026-27.pdf    official schedule (source data, not a prediction)
styles.css            dashboard styling
requirements.txt      Python dependencies
```

## Regenerating models

The trained artifacts in `backend/artifacts/` are git-ignored. Re-run `npm run train`
after changing a dataset or a trainer. The API loads artifacts lazily on first request,
so restart `npm run api` (or `npm run dev:all`) after retraining to pick up new models.
