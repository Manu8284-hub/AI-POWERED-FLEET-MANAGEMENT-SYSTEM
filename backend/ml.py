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

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

WEATHERS = [
    "Clear",
    "Cloudy",
    "Rain",
]

CLASS_ORDER = [
    "LOW",
    "MEDIUM",
    "HIGH",
]

PUBLISHED_ROUTES = 127


def _load_json(name):
    return json.loads((ART / name).read_text())


class FleetModels:

    def __init__(self):

        # ---------------------------------------------------------
        # Check required model artifacts
        # ---------------------------------------------------------
        missing = [
            f
            for f in (
                "demand.joblib",
                "occupancy.joblib",
                "clusters.json",
                "route_defaults.json",
            )
            if not (ART / f).exists()
        ]

        if missing:
            raise FileNotFoundError(
                f"Missing model artifacts {missing}. "
                "Run `npm run train` (python backend/train.py) first."
            )

        # ---------------------------------------------------------
        # Load trained models
        # ---------------------------------------------------------
        self.demand = joblib.load(
            ART / "demand.joblib"
        )

        self.occupancy = joblib.load(
            ART / "occupancy.joblib"
        )

        # ---------------------------------------------------------
        # Load model metadata
        # ---------------------------------------------------------
        self.demand_meta = _load_json(
            "demand_meta.json"
        )

        self.occupancy_meta = _load_json(
            "occupancy_meta.json"
        )

        # ---------------------------------------------------------
        # Load route defaults
        # ---------------------------------------------------------
        rd = _load_json(
            "route_defaults.json"
        )

        self.route_defaults = rd["routes"]

        self.default_capacity = rd[
            "default_capacity"
        ]

        # ---------------------------------------------------------
        # Load clustering results
        # ---------------------------------------------------------
        self.clusters = _load_json(
            "clusters.json"
        )

        # Routes for which we actually have training data.
        # route_defaults keys are stored as strings.
        self.route_ids = sorted(
            int(r)
            for r in self.route_defaults
        )

        # Occupancy model class order
        self._occ_classes = list(
            self.occupancy.named_steps[
                "model"
            ].classes_
        )

        # Cache for network context
        self._ctx_cache = {}

    # =========================================================
    # FEATURE CONSTRUCTION
    # =========================================================

    def _row(
        self,
        route,
        day,
        weather,
        capacity=None
    ):
        """
        Build one prediction row.

        IMPORTANT:
        Route_ID and Stop_ID are categorical features.
        They must be strings because the trained demand and
        occupancy pipelines were trained with string categorical
        values.
        """

        route_key = str(int(route))

        rd = self.route_defaults.get(
            route_key
        )

        if rd:

            stop_id = str(
                rd["stop_id"]
            )

            cap = (
                capacity
                or rd["capacity"]
            )

        else:

            # Route with no training data.
            # Use a graceful baseline.
            stop_id = (
                f"R{route_key}_S01"
            )

            cap = (
                capacity
                or self.default_capacity
            )

        return {
            "Route_ID": route_key,
            "Stop_ID": str(stop_id),
            "Day": day,
            "Weather": weather,
            "Bus_Capacity": int(cap),
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    @staticmethod
    def _valid(
        day,
        weather
    ):

        return (
            day
            if day in DAYS
            else "Monday",
            weather
            if weather in WEATHERS
            else "Clear",
        )

    # =========================================================
    # SINGLE ROUTE: DEMAND
    # =========================================================

    def predict_demand(
        self,
        route,
        day,
        weather,
        capacity=None
    ):

        day, weather = self._valid(
            day,
            weather
        )

        X = pd.DataFrame([
            self._row(
                route,
                day,
                weather,
                capacity
            )
        ])

        value = float(
            self.demand.predict(X)[0]
        )

        cap = int(
            X["Bus_Capacity"].iat[0]
        )

        return {
            "route": int(route),
            "day": day,
            "weather": weather,
            "capacity": cap,
            "predicted_passengers": round(
                value,
                1
            ),
            "load_pct": round(
                min(value / cap, 2.0) * 100,
                1
            ),
            "known_route": (
                str(int(route))
                in self.route_defaults
            ),
        }

    # =========================================================
    # SINGLE ROUTE: OCCUPANCY
    # =========================================================

    def predict_occupancy(
        self,
        route,
        day,
        weather,
        capacity=None
    ):

        day, weather = self._valid(
            day,
            weather
        )

        X = pd.DataFrame([
            self._row(
                route,
                day,
                weather,
                capacity
            )
        ])

        proba = self.occupancy.predict_proba(
            X
        )[0]

        probs = {
            c: round(
                float(p),
                3
            )
            for c, p in zip(
                self._occ_classes,
                proba
            )
        }

        category = max(
            probs,
            key=probs.get
        )

        return {
            "route": int(route),
            "day": day,
            "weather": weather,
            "category": category,
            "probabilities": probs,
        }

    # =========================================================
    # WHOLE NETWORK CONTEXT
    # =========================================================

    def context(
        self,
        day,
        weather
    ):

        day, weather = self._valid(
            day,
            weather
        )

        key = (
            day,
            weather
        )

        if key in self._ctx_cache:
            return self._ctx_cache[key]

        # Build one row per known route.
        X = pd.DataFrame([
            self._row(
                r,
                day,
                weather
            )
            for r in self.route_ids
        ])

        # Demand prediction
        demand = self.demand.predict(
            X
        )

        # Occupancy prediction
        occ = self.occupancy.predict(
            X
        )

        caps = X[
            "Bus_Capacity"
        ].to_numpy(
            dtype=float
        )

        load = demand / caps

        # ---------------------------------------------------------
        # Per-route results
        # ---------------------------------------------------------
        per_route = []

        for i, r in enumerate(
            self.route_ids
        ):

            per_route.append({

                "route": r,

                "stop_name": self.route_defaults[
                    str(r)
                ]["stop_name"],

                "demand": round(
                    float(demand[i]),
                    1
                ),

                "capacity": int(
                    caps[i]
                ),

                "load_pct": round(
                    float(load[i]) * 100,
                    1
                ),

                "category": str(
                    occ[i]
                ),
            })

        # ---------------------------------------------------------
        # Occupancy counts
        # ---------------------------------------------------------
        counts = {
            c: int(
                (occ == c).sum()
            )
            for c in CLASS_ORDER
        }

        # ---------------------------------------------------------
        # Network result
        # ---------------------------------------------------------
        result = {

            "day": day,

            "weather": weather,

            "riders": int(
                round(
                    demand.sum()
                )
            ),

            "high_risk": counts[
                "HIGH"
            ],

            "occupancy_counts": counts,

            "avg_load": round(
                float(
                    load.mean()
                ) * 100,
                1
            ),

            "efficiency": round(
                float(
                    np.minimum(
                        load,
                        1.0
                    ).mean()
                ) * 100,
                1
            ),

            "active_buses": int(
                (load > 0.4).sum()
            ),

            "per_route": per_route,
        }

        self._ctx_cache[key] = result

        return result

    # =========================================================
    # OVERVIEW
    # =========================================================

    def overview(
        self,
        day,
        weather
    ):

        ctx = self.context(
            day,
            weather
        )

        # Peak day for this weather
        by_day = {
            d: self.context(
                d,
                weather
            )["riders"]
            for d in DAYS
        }

        peak_day = max(
            by_day,
            key=by_day.get
        )

        return {

            "day": ctx["day"],

            "weather": ctx["weather"],

            "published_routes": PUBLISHED_ROUTES,

            "modelled_routes": len(
                self.route_ids
            ),

            "riders": ctx["riders"],

            "high_risk": ctx["high_risk"],

            "efficiency": ctx["efficiency"],

            "avg_load": ctx["avg_load"],

            "occupancy_counts": ctx[
                "occupancy_counts"
            ],

            "peak_day": peak_day,

            "peak_riders": by_day[
                peak_day
            ],

            "metrics": {

                "demand_r2": round(
                    self.demand_meta[
                        "random_forest"
                    ]["r2"],
                    3
                ),

                "demand_mae": round(
                    self.demand_meta[
                        "random_forest"
                    ]["mae"],
                    2
                ),

                "occupancy_accuracy": round(
                    self.occupancy_meta[
                        "accuracy"
                    ],
                    3
                ),

                "cluster_silhouette": round(
                    self.clusters[
                        "silhouette"
                    ],
                    3
                ),
            },
        }

    # =========================================================
    # WEEKLY FORECAST
    # =========================================================

    def forecast(
        self,
        weather,
        route=None
    ):

        _, weather = self._valid(
            "Monday",
            weather
        )

        if (
            route is not None
            and str(route).strip() != ""
        ):

            demand = [
                self.predict_demand(
                    route,
                    d,
                    weather
                )["predicted_passengers"]
                for d in DAYS
            ]

            cap = self.predict_demand(
                route,
                "Monday",
                weather
            )["capacity"]

            capacity = [
                cap
            ] * len(DAYS)

            scope = (
                f"Route {int(route):02d}"
            )

        else:

            demand = [
                self.context(
                    d,
                    weather
                )["riders"]
                for d in DAYS
            ]

            total_cap = int(
                sum(
                    self.route_defaults[
                        str(r)
                    ]["capacity"]
                    for r in self.route_ids
                )
            )

            capacity = [
                total_cap
            ] * len(DAYS)

            scope = "Network"

        peak_i = int(
            np.argmax(demand)
        )

        return {

            "days": DAYS,

            "demand": demand,

            "capacity": capacity,

            "weather": weather,

            "scope": scope,

            "peak_day": DAYS[
                peak_i
            ],

            "peak_value": demand[
                peak_i
            ],
        }

    # =========================================================
    # CLUSTERS
    # =========================================================

    def cluster_view(self):

        return self.clusters

    # =========================================================
    # RECOMMENDATIONS
    # =========================================================

    def recommendations(
        self,
        day,
        weather
    ):

        ctx = self.context(
            day,
            weather
        )

        routes = ctx[
            "per_route"
        ]

        recs = []

        # ---------------------------------------------------------
        # Overloaded routes
        # ---------------------------------------------------------
        overloaded = sorted(
            [
                r
                for r in routes
                if r["demand"] > r["capacity"]
            ],
            key=lambda r:
                r["demand"] - r["capacity"],
            reverse=True
        )

        for r in overloaded[:2]:

            over = round(
                r["demand"]
                - r["capacity"]
            )

            recs.append({

                "title":
                    f"Add relief capacity to Route "
                    f"{r['route']:02d}",

                "description":
                    f"Predicted {round(r['demand'])} "
                    f"passengers vs {r['capacity']} seats "
                    f"({r['stop_name']}) — over by "
                    f"{over} on {day}.",

                "tag": "HIGH IMPACT",

                "urgent": True,

                "route": r["route"],
            })

        # ---------------------------------------------------------
        # Low-load routes
        # ---------------------------------------------------------
        idle = sorted(
            [
                r
                for r in routes
                if r["load_pct"] < 45
            ],
            key=lambda r:
                r["load_pct"]
        )

        if len(idle) >= 2:

            a, b = idle[0], idle[1]

            recs.append({

                "title":
                    f"Combine trips on Routes "
                    f"{a['route']:02d} & "
                    f"{b['route']:02d}",

                "description":
                    f"Both under "
                    f"{round(max(a['load_pct'], b['load_pct']))}% "
                    f"predicted load — a shared service "
                    f"is viable {day.lower()}.",

                "tag": "SAVES 1 BUS",

                "urgent": False,

                "route": a["route"],
            })

        elif idle:

            r = idle[0]

            recs.append({

                "title":
                    f"Right-size Route "
                    f"{r['route']:02d}",

                "description":
                    f"Only {round(r['load_pct'])}% "
                    f"predicted load "
                    f"({r['stop_name']}) — a smaller "
                    f"bus cuts idle capacity.",

                "tag": "EFFICIENCY",

                "urgent": False,

                "route": r["route"],
            })

        # ---------------------------------------------------------
        # Balanced route
        # ---------------------------------------------------------
        mid = sorted(
            [
                r
                for r in routes
                if 45 <= r["load_pct"] <= 85
            ],
            key=lambda r:
                abs(
                    r["load_pct"] - 70
                )
        )

        if mid:

            r = mid[0]

            recs.append({

                "title":
                    f"Hold current allocation "
                    f"on Route {r['route']:02d}",

                "description":
                    f"Predicted {round(r['load_pct'])}% "
                    f"load is well matched to capacity — "
                    f"no change needed.",

                "tag": "BALANCED",

                "urgent": False,

                "route": r["route"],
            })

        return {
            "day": day,
            "weather": weather,
            "recommendations": recs[:4],
        }

    # =========================================================
    # LIVE TELEMETRY
    # =========================================================

    def live_tick(
        self,
        day,
        weather,
        tick
    ):

        ctx = self.context(
            day,
            weather
        )

        wave = math.sin(
            tick / 6.0
        )

        riders = int(
            ctx["riders"]
            * (1 + 0.03 * wave)
            + random.uniform(-8, 8)
        )

        # Keep high-risk count equal to baseline.
        high = ctx["high_risk"]

        efficiency = round(
            min(
                99.4,
                max(
                    55.0,
                    ctx["efficiency"]
                    + wave * 1.4
                    + random.uniform(
                        -0.4,
                        0.4
                    )
                )
            ),
            1
        )

        active = (
            12
            + int(
                round(
                    4 * (wave + 1)
                )
            )
        )

        return {

            "ts": tick,

            "day": day,

            "weather": weather,

            "riders": riders,

            "high_risk": high,

            "efficiency": efficiency,

            "active_buses": active,

            "baseline_riders":
                ctx["riders"],
        }


# =============================================================
# GLOBAL MODEL INSTANCE
# =============================================================

_MODELS = None


def get_models():

    global _MODELS

    if _MODELS is None:
        _MODELS = FleetModels()

    return _MODELS