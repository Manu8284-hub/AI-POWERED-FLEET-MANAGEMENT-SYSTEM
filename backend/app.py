"""FleetIQ API — serves real model predictions to the dashboard.

Endpoints under /api. `/api/stream` is a Server-Sent Events feed that pushes a
fresh snapshot every few seconds: the numbers are real model predictions for
the selected day/weather with a small, deterministic-ish live fluctuation on
top (there is no live GPS/sensor feed in this project — the datasets are
fixed, so the "live" motion is simulated telemetry over genuine predictions).
"""

import asyncio
import json

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .ml import get_models, DAYS, WEATHERS, PUBLISHED_ROUTES

app = FastAPI(title="FleetIQ API", version="1.0.0")

# CORS is a fallback; in dev the Vite proxy serves /api same-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

STREAM_INTERVAL_SECONDS = 3


class PredictIn(BaseModel):
    route: int
    day: str = "Monday"
    weather: str = "Clear"
    capacity: int | None = None


@app.get("/api/health")
def health():
    try:
        m = get_models()
        return {"status": "ok", "models_loaded": True,
                "modelled_routes": len(m.route_ids)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "models_loaded": False, "detail": str(exc)}


@app.get("/api/context")
def context():
    m = get_models()
    return {
        "days": DAYS,
        "weathers": WEATHERS,
        "published_routes": PUBLISHED_ROUTES,
        "modelled_routes": len(m.route_ids),
        "route_ids": m.route_ids,
        "stream_interval": STREAM_INTERVAL_SECONDS,
        "metrics": {
            "demand_r2": round(m.demand_meta["random_forest"]["r2"], 3),
            "demand_mae": round(m.demand_meta["random_forest"]["mae"], 2),
            "occupancy_accuracy": round(m.occupancy_meta["accuracy"], 3),
            "cluster_silhouette": round(m.clusters["silhouette"], 3),
        },
    }


@app.get("/api/overview")
def overview(day: str = "Monday", weather: str = "Clear"):
    return get_models().overview(day, weather)


@app.get("/api/demand/forecast")
def forecast(weather: str = "Clear", route: str | None = Query(default=None)):
    route_val = int(route) if route not in (None, "", "null") else None
    return get_models().forecast(weather, route_val)


@app.post("/api/predict/demand")
def predict_demand(body: PredictIn):
    return get_models().predict_demand(body.route, body.day, body.weather, body.capacity)


@app.post("/api/predict/occupancy")
def predict_occupancy(body: PredictIn):
    return get_models().predict_occupancy(body.route, body.day, body.weather, body.capacity)


@app.get("/api/clusters")
def clusters():
    return get_models().cluster_view()


@app.get("/api/recommendations")
def recommendations(day: str = "Monday", weather: str = "Clear"):
    return get_models().recommendations(day, weather)


@app.post("/api/optimise")
def optimise(day: str = "Monday", weather: str = "Clear"):
    result = get_models().recommendations(day, weather)
    urgent = sum(1 for r in result["recommendations"] if r["urgent"])
    result["prepared"] = len(result["recommendations"])
    result["urgent"] = urgent
    return result


@app.get("/api/stream")
async def stream(day: str = "Monday", weather: str = "Clear"):
    m = get_models()

    async def event_generator():
        tick = 0
        while True:
            payload = m.live_tick(day, weather, tick)
            yield f"data: {json.dumps(payload)}\n\n"
            tick += 1
            await asyncio.sleep(STREAM_INTERVAL_SECONDS)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                 "X-Accel-Buffering": "no"},
    )
