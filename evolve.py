"""
Evolutionary search loop using OpenEvolve.

Usage (activate env first):
    conda activate <env_name>
    python evolve.py

Or via CLI:
    openevolve-run solvers/baseline_backtracking.py openevolve_evaluate.py --config config.yaml --output results
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from openevolve import OpenEvolve
from openevolve.config import load_config


async def main():
    config = load_config("config.yaml")

    oe = OpenEvolve(
        initial_program_path="solvers/baseline_backtracking.py",
        evaluation_file="openevolve_evaluate.py",
        config=config,
        output_dir="results",
    )

    print("Starting evolution from baseline_backtracking solver...")
    best = await oe.run(iterations=config.max_iterations)

    print("\nEvolution complete. Best program metrics:")
    for k, v in best.metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
