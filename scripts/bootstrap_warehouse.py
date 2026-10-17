"""Build the upstream cx-journey-warehouse; copy its DuckDB file and semantic manifest into data/.

    python scripts/bootstrap_warehouse.py [--scale 1.0] [--repo PATH_OR_URL] [--ref COMMIT]

The upstream commit is pinned so the schema and metric catalogue the models see (and so the
recorded responses CI replays) stay exactly the ones the published run used.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "https://github.com/qasimrazamalik-coder/cx-journey-warehouse.git"
PINNED_REF = "3f62ba933e52f72a09ccd89acd1f39fc99518159"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--ref", default=PINNED_REF, help="upstream commit to build (ignored for a local path)")
    parser.add_argument("--scale", default="1.0")
    args = parser.parse_args()

    if Path(args.repo).exists():
        upstream = Path(args.repo).resolve()
    else:
        upstream = ROOT / ".cache" / "cx-journey-warehouse"
        if not upstream.exists():
            upstream.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", "-q", args.repo, str(upstream)], check=True)
        else:
            subprocess.run(["git", "-C", str(upstream), "fetch", "-q", "origin"], check=True)
        subprocess.run(["git", "-C", str(upstream), "checkout", "-q", args.ref], check=True)

    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    built = upstream / "warehouse_for_benchmark.duckdb"
    subprocess.run([sys.executable, "scripts/build.py", "--scale", args.scale, "--db", str(built), "--skip-report"],
                   cwd=upstream, check=True)
    shutil.copyfile(built, data / "warehouse.duckdb")
    built.unlink()
    shutil.copyfile(upstream / "dbt" / "target" / "semantic_manifest.json", data / "semantic_manifest.json")
    print(f"ready: {data / 'warehouse.duckdb'} and {data / 'semantic_manifest.json'}")


if __name__ == "__main__":
    main()
