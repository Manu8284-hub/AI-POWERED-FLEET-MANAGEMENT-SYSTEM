"""Model loading + prediction/aggregation helpers for the FleetIQ API.

Loads the persisted artifacts once, then answers everything the dashboard
needs: single-route predictions, whole-network context aggregates (cached per
day+weather), the weekly forecast series, fleet recommendations, and the live
telemetry tick used by the SSE stream.
"""

import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

ART = Path(__file__).resolve().parent / "artifacts"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEATHERS = ["Clear", "Cloudy", "Rain"]
CLASS_ORDER = ["LOW", "MEDIUM", "HIGH"]
PUBLISHED_ROUTES = 127


def _load_json(name):
    return json.loads((ART / name).read_text())


class FleetModels:
    def __init__(self):
        missing = [f for f in ("demand.joblib", "occupancy.joblib", "clusters.json",
                               "route_defaults.json") if not (ART / f).exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing model artifacts {missing}. Run `npm run train` (python backend/train.py) first."
            )
        self.demand = joblib.load(ART / "demand.joblib")
        self.occupancy = joblib.load(ART / "occupancy.joblib")
        self.demand_meta = _load_json("demand_meta.json")
        self.occupancy_meta = _load_json("occupancy_meta.json")
        rd = _load_json("route_defaults.json")
        self.route_defaults = rd["routes"]
        self.default_capacity = rd["default_capacity"]
        self.clusters = _load_json("clusters.json")
        # Routes we actually have training data for -> the "network".
        self.route_ids = sorted(int(r) for r in self.route_defaults)
        self._occ_classes = list(self.occupancy.named_steps["model"].classes_)
        self._ctx_cache = {}

    # ---- feature construction -------------------------------------------
    def _row(self, route, day, weather, capacity=None):
        rd = self.route_defaults.get(str(int(route)))
        if rd:
            stop_id, cap = rd["stop_id"], (capacity or rd["capacity"])
        else:  # route with no training data -> graceful baseline
            stop_id, cap = f"R{int(route)}_S01", (capacity or self.default_capacity)
        return {"Route_ID": int(route), "Stop_ID": stop_id, "Day": day,
                "Weather": weather, "Bus_Capacity": int(cap)}

    @staticmethod
    def _valid(day, weather):
        return (day if day in DAYS else "Monday",
                weather if weather in WEATHERS else "Clear")

    # ---- single-route predictions ---------------------------------------
    def predict_demand(self, route, day, weather, capacity=None):
        day, weather = self._valid(day, weather)
        X = pd.DataFrame([self._row(route, day, weather, capacity)])
        value = float(self.demand.predict(X)[0])
        cap = int(X["Bus_Capacity"].iat[0])
        return {"route": int(route), "day": day, "weather": weather, "capacity": cap,
                "predicted_passengers": round(value, 1),
                "load_pct": round(min(value / cap, 2.0) * 100, 1),
                "known_route": str(int(route)) in self.route_defaults}

    def predict_occupancy(self, route, day, weather, capacity=None):
        day, weather = self._valid(day, weather)
        X = pd.DataFrame([self._row(route, day, weather, capacity)])
        proba = self.occupancy.predict_proba(X)[0]
        probs = {c: round(float(p), 3) for c, p in zip(self._occ_classes, proba)}
        category = max(probs, key=probs.get)
        return {"route": int(route), "day": day, "weather": weather,
                "category": category, "probabilities": probs}

    # ---- whole-network context (cached) ---------------------------------
    def context(self, day, weather):
        day, weather = self._valid(day, weather)
        key = (day, weather)
        if key in self._ctx_cache:
            return self._ctx_cache[key]

        X = pd.DataFrame([self._row(r, day, weather) for r in self.route_ids])
        demand = self.demand.predict(X)
        occ = self.occupancy.predict(X)
        caps = X["Bus_Capacity"].to_numpy(dtype=float)
        load = demand / caps

        per_route = []
        for i, r in enumerate(self.route_ids):
            per_route.append({
                "route": r,
                "stop_name": self.route_defaults[str(r)]["stop_name"],
                "demand": round(float(demand[i]), 1),
                "capacity": int(caps[i]),
                "load_pct": round(float(load[i]) * 100, 1),
                "category": str(occ[i]),
            })

        counts = {c: int((occ == c).sum()) for c in CLASS_ORDER}
        result = {
            "day": day, "weather": weather,
            "riders": int(round(demand.sum())),
            "high_risk": counts["HIGH"],
            "occupancy_counts": counts,
            "avg_load": round(float(load.mean()) * 100, 1),
            "efficiency": round(float(np.minimum(load, 1.0).mean()) * 100, 1),
            "active_buses": int((load > 0.4).sum()),
            "per_route": per_route,
        }
        self._ctx_cache[key] = result
        return result

    # ---- overview (stat cards + occupancy panel) ------------------------
    def overview(self, day, weather):
        ctx = self.context(day, weather)
        # peak day for this weather (network riders across the week)
        by_day = {d: self.context(d, weather)["riders"] for d in DAYS}
        peak_day = max(by_day, key=by_day.get)
        return {
            "day": ctx["day"], "weather": ctx["weather"],
            "published_routes": PUBLISHED_ROUTES,
            "modelled_routes": len(self.route_ids),
            "riders": ctx["riders"],
            "high_risk": ctx["high_risk"],
            "efficiency": ctx["efficiency"],
            "avg_load": ctx["avg_load"],
            "occupancy_counts": ctx["occupancy_counts"],
            "peak_day": peak_day,
            "peak_riders": by_day[peak_day],
            "metrics": {
                "demand_r2": round(self.demand_meta["random_forest"]["r2"], 3),
                "demand_mae": round(self.demand_meta["random_forest"]["mae"], 2),
                "occupancy_accuracy": round(self.occupancy_meta["accuracy"], 3),
                "cluster_silhouette": round(self.clusters["silhouette"], 3),
            },
        }

    # ---- weekly forecast for the line chart -----------------------------
    def forecast(self, weather, route=None):
        _, weather = self._valid("Monday", weather)
        if route is not None and str(route).strip() != "":
            demand = [self.predict_demand(route, d, weather)["predicted_passengers"] for d in DAYS]
            cap = self.predict_demand(route, "Monday", weather)["capacity"]
            capacity = [cap] * len(DAYS)
            scope = f"Route {int(route):02d}"
        else:
            demand = [self.context(d, weather)["riders"] for d in DAYS]
            total_cap = int(sum(self.route_defaults[str(r)]["capacity"] for r in self.route_ids))
            capacity = [total_cap] * len(DAYS)
            scope = "Network"
        peak_i = int(np.argmax(demand))
        return {"days": DAYS, "demand": demand, "capacity": capacity,
                "weather": weather, "scope": scope,
                "peak_day": DAYS[peak_i], "peak_value": demand[peak_i]}

    # ---- clusters -------------------------------------------------------
    def cluster_view(self):
        return self.clusters

    # ---- recommendations ------------------------------------------------
    def recommendations(self, day, weather):
        ctx = self.context(day, weather)
        routes = ctx["per_route"]
        recs = []

        overloaded = sorted([r for r in routes if r["demand"] > r["capacity"]],
                            key=lambda r: r["demand"] - r["capacity"], reverse=True)
        for r in overloaded[:2]:
            over = round(r["demand"] - r["capacity"])
            recs.append({
                "title": f"Add relief capacity to Route {r['route']:02d}",
                "description": f"Predicted {round(r['demand'])} passengers vs {r['capacity']} seats "
                               f"({r['stop_name']}) — over by {over} on {day}.",
                "tag": "HIGH IMPACT", "urgent": True, "route": r["route"],
            })

        idle = sorted([r for r in routes if r["load_pct"] < 45],
                     key=lambda r: r["load_pct"])
        if len(idle) >= 2:
            a, b = idle[0], idle[1]
            recs.append({
                "title": f"Combine trips on Routes {a['route']:02d} & {b['route']:02d}",
                "description": f"Both under {round(max(a['load_pct'], b['load_pct']))}% predicted load — "
                               f"a shared service is viable {day.lower()}.",
                "tag": "SAVES 1 BUS", "urgent": False, "route": a["route"],
            })
        elif idle:
            r = idle[0]
            recs.append({
                "title": f"Right-size Route {r['route']:02d}",
                "description": f"Only {round(r['load_pct'])}% predicted load ({r['stop_name']}) — "
                               f"a smaller bus cuts idle capacity.",
                "tag": "EFFICIENCY", "urgent": False, "route": r["route"],
            })

        # A mid-load balancing suggestion to round things out.
        mid = sorted([r for r in routes if 45 <= r["load_pct"] <= 85],
                    key=lambda r: abs(r["load_pct"] - 70))
        if mid:
            r = mid[0]
            recs.append({
                "title": f"Hold current allocation on Route {r['route']:02d}",
                "description": f"Predicted {round(r['load_pct'])}% load is well matched to capacity — no change needed.",
                "tag": "BALANCED", "urgent": False, "route": r["route"],
            })
        return {"day": day, "weather": weather, "recommendations": recs[:4]}

    # ---- live telemetry tick (simulated over real predictions) ----------
    def live_tick(self, day, weather, tick):
        ctx = self.context(day, weather)
        wave = math.sin(tick / 6.0)
        riders = int(ctx["riders"] * (1 + 0.03 * wave) + random.uniform(-8, 8))
        # high_risk is a discrete occupancy-classification count; keep it equal to
        # the baseline so the live stat card stays in sync with the occupancy panel.
        high = ctx["high_risk"]
        efficiency = round(min(99.4, max(55.0, ctx["efficiency"] + wave * 1.4 + random.uniform(-0.4, 0.4))), 1)
        active = 12 + int(round(4 * (wave + 1)))  # 12..20 buses in service
        return {
            "ts": tick,
            "day": day, "weather": weather,
            "riders": riders,
            "high_risk": high,
            "efficiency": efficiency,
            "active_buses": active,
            "baseline_riders": ctx["riders"],
        }


_MODELS = None


def get_models():
    global _MODELS
    if _MODELS is None:
        _MODELS = FleetModels()
    return _MODELS
