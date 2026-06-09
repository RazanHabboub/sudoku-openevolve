"""
OpenEvolve evaluation bridge.

Called by OpenEvolve with a path to a temporary solver file.
Exposes evaluate(program_path) -> dict.

Puzzle tiers (150 total):
  easy   (100) – puzzles0_kaggle
  hard   (25)  – puzzles5_forum_hardest_1905_11+
  expert (25)  – puzzles6_forum_hardest_1106

Each puzzle is solved under a 1-second per-puzzle timeout enforced via a
daemon thread; timed-out puzzles count as unsolved.

combined_score weights harder tiers more heavily to create selection
pressure for algorithmic improvement beyond simple backtracking.
Speed is measured only on successfully solved puzzles.
"""

import csv
import importlib.util
import os
import threading
import time
from queue import Empty, Queue

PUZZLES_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eval_puzzles.csv")
PUZZLE_TIMEOUT = 1.0  # seconds per puzzle

# Difficulty weights must sum to 1.0
TIER_WEIGHTS = {"easy": 0.2, "hard": 0.4, "expert": 0.4}


def _puzzle_to_grid(puzzle_str):
    return [[int(puzzle_str[r * 9 + c]) for c in range(9)] for r in range(9)]


def _is_valid_solution(original, solved):
    if solved is None:
        return False
    nums = set(range(1, 10))
    for r in range(9):
        for c in range(9):
            if original[r][c] != 0 and original[r][c] != solved[r][c]:
                return False
    for i in range(9):
        if set(solved[i]) != nums:
            return False
        if {solved[r][i] for r in range(9)} != nums:
            return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            box = [solved[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)]
            if set(box) != nums:
                return False
    return True


def _solve_with_timeout(solve_fn, grid, timeout):
    """Run solve_fn in a daemon thread; return (result, elapsed) or (None, timeout) on timeout."""
    result_q = Queue()

    def _target():
        t0 = time.perf_counter()
        try:
            result_q.put((solve_fn(grid), time.perf_counter() - t0))
        except Exception:
            result_q.put((None, time.perf_counter() - t0))

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    try:
        return result_q.get(timeout=timeout)
    except Empty:
        return None, timeout


def evaluate(program_path):
    try:
        spec = importlib.util.spec_from_file_location("evolved_solver", program_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        solve_fn = module.solve
    except Exception:
        return _zero_metrics()

    tier_solved = {t: 0   for t in TIER_WEIGHTS}
    tier_total  = {t: 0   for t in TIER_WEIGHTS}
    tier_time   = {t: 0.0 for t in TIER_WEIGHTS}  # time for solved puzzles only

    try:
        with open(PUZZLES_CSV, newline="") as f:
            for row in csv.DictReader(f):
                tier = row["difficulty"]
                original = _puzzle_to_grid(row["puzzle"])
                tier_total[tier] += 1

                result, elapsed = _solve_with_timeout(solve_fn, original, PUZZLE_TIMEOUT)

                if _is_valid_solution(original, result):
                    tier_solved[tier] += 1
                    tier_time[tier] += elapsed
    except Exception:
        return _zero_metrics()

    # Per-tier solve rates
    easy_rate   = tier_solved["easy"]   / tier_total["easy"]   if tier_total["easy"]   else 0.0
    hard_rate   = tier_solved["hard"]   / tier_total["hard"]   if tier_total["hard"]   else 0.0
    expert_rate = tier_solved["expert"] / tier_total["expert"] if tier_total["expert"] else 0.0

    # Per-tier avg time (over solved puzzles only; 0.0 if none solved)
    easy_avg_time   = tier_time["easy"]   / tier_solved["easy"]   if tier_solved["easy"]   else 0.0
    hard_avg_time   = tier_time["hard"]   / tier_solved["hard"]   if tier_solved["hard"]   else 0.0
    expert_avg_time = tier_time["expert"] / tier_solved["expert"] if tier_solved["expert"] else 0.0

    # Difficulty-weighted correctness score
    correctness = (
        TIER_WEIGHTS["easy"]   * easy_rate +
        TIER_WEIGHTS["hard"]   * hard_rate +
        TIER_WEIGHTS["expert"] * expert_rate
    )

    # Speed over all solved puzzles only
    total_solved = sum(tier_solved.values())
    avg_time_solved = sum(tier_time.values()) / total_solved if total_solved else 999.0
    speed_score = 1.0 / (1.0 + avg_time_solved * 10)  # 100ms → 0.50; 10ms → 0.91

    combined_score = 0.7 * correctness + 0.3 * speed_score

    return {
        "easy_rate":        easy_rate,
        "hard_rate":        hard_rate,
        "expert_rate":      expert_rate,
        "correctness":      correctness,
        "easy_avg_time":    easy_avg_time,
        "hard_avg_time":    hard_avg_time,
        "expert_avg_time":  expert_avg_time,
        "speed_score":      speed_score,
        "combined_score":   combined_score,
    }


def _zero_metrics():
    return {
        "easy_rate": 0.0, "hard_rate": 0.0, "expert_rate": 0.0,
        "correctness": 0.0, "easy_avg_time": 0.0, "hard_avg_time": 0.0,
        "expert_avg_time": 0.0, "speed_score": 0.0, "combined_score": 0.0,
    }
