"""Train all three FleetIQ models in one shot (used by `npm run train`).

Runs each model's own train.py as an isolated subprocess so their EDA output
is preserved and the artifacts land in backend/artifacts/.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "demand_model" / "train.py",
    ROOT / "occupancy_model" / "train.py",
    ROOT / "Bus_Stop_Clustering_Model" / "train.py",
]


def main():
    for script in SCRIPTS:
        rel = script.relative_to(ROOT)
        print(f"\n{'=' * 72}\n Training: {rel}\n{'=' * 72}", flush=True)
        result = subprocess.run([sys.executable, str(script)], cwd=str(script.parent))
        if result.returncode != 0:
            print(f"\n!! {rel} failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)
    print(f"\n{'=' * 72}\n All models trained. Artifacts -> {ROOT / 'backend' / 'artifacts'}\n{'=' * 72}")


if __name__ == "__main__":
    main()
