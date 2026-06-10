"""
OpenEvolve evaluation bridge -- backtrack-efficiency metric.

Called by OpenEvolve with a path to a temporary solver file.
Exposes evaluate(program_path) -> dict.

Puzzle set: 150 puzzles (100 easy / 25 hard / 25 expert), no tier weighting.

Fitness signal:
  - Each solved puzzle contributes its actual BACKTRACKS count.
  - Each unsolved or timed-out puzzle contributes BACKTRACK_CAP (1,500,000).
  - avg_bt  = sum(puzzle_bt) / num_total          (denominator = ALL puzzles)
  - efficiency = 1 / (1 + avg_bt / SCALE)
  - combined_score = efficiency                   (OpenEvolve maximises this)

SCALE is set to the baseline backtracking solver's avg_bt so it starts at ~0.5.
Tier solve rates are returned as secondary metrics for logging/analysis only.
"""

import csv
import importlib.util
import logging
import os
import re
import threading
import time
import types
from queue import Empty, Queue

_log = logging.getLogger(__name__)

PUZZLES_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eval_puzzles.csv")
PUZZLE_TIMEOUT = 1.5        # seconds per puzzle
BACKTRACK_CAP  = 1_500_000  # sentinel for unsolved / timed-out puzzles
SCALE          = 303_708    # baseline avg_bt; efficiency ~0.50 for baseline


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


def _solve_with_timeout(solve_fn, module, grid, timeout):
    """
    Run solve_fn in a daemon thread.
    Returns (result, elapsed, bt) where bt is read inside the thread
    immediately after solve_fn returns -- safe from cross-puzzle contamination.
    On timeout returns (None, timeout, None); caller uses BACKTRACK_CAP.
    """
    result_q = Queue()

    def _target():
        t0 = time.perf_counter()
        try:
            result = solve_fn(grid)
            bt = getattr(module, "BACKTRACKS", 0)
            result_q.put((result, time.perf_counter() - t0, bt))
        except Exception:
            result_q.put((None, time.perf_counter() - t0, 0))

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    try:
        return result_q.get(timeout=timeout)
    except Empty:
        return None, timeout, None  # None bt -> caller uses BACKTRACK_CAP


_DEBUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "debug_solvers")


def _load_module(program_path):
    """Load solver module, extracting code from markdown fences if present."""
    with open(program_path, "r", encoding="utf-8") as f:
        raw = f.read()
    # Extract content from ```python ... ``` or ``` ... ``` block if present.
    # This handles Gemini responses with preamble text before the code block.
    m = re.search(r"```(?:python)?\s*\n(.*?)```", raw, re.DOTALL)
    if m:
        code = m.group(1).rstrip()
    else:
        # No closing fence (e.g. truncated response) — strip any opening fence.
        code = re.sub(r"^```(?:python)?\s*\n?", "", raw.strip())
        code = code.rstrip().rstrip("`").rstrip()
    module = types.ModuleType("evolved_solver")
    try:
        exec(compile(code, program_path, "exec"), module.__dict__)
    except Exception as e:
        # Save the failing code for post-mortem inspection.
        try:
            os.makedirs(_DEBUG_DIR, exist_ok=True)
            base = os.path.basename(program_path).replace(".py", "")
            debug_path = os.path.join(_DEBUG_DIR, f"fail_{base}_{int(time.time())}.py")
            with open(debug_path, "w", encoding="utf-8") as df:
                df.write(f"# Error: {e}\n# --- raw LLM output below ---\n{raw}\n# --- extracted code ---\n{code}")
        except Exception:
            pass
        _log.warning("Load error for %s: %s", program_path, e)
        raise
    return module


def evaluate(program_path):
    try:
        module = _load_module(program_path)
        solve_fn = module.solve
    except Exception:
        return _zero_metrics()

    puzzle_bt   = []
    tier_solved = {"easy": 0, "hard": 0, "expert": 0}
    tier_total  = {"easy": 0, "hard": 0, "expert": 0}

    try:
        with open(PUZZLES_CSV, newline="") as f:
            for row in csv.DictReader(f):
                tier     = row["difficulty"]
                original = _puzzle_to_grid(row["puzzle"])
                tier_total[tier] += 1

                result, _elapsed, bt = _solve_with_timeout(solve_fn, module, original, PUZZLE_TIMEOUT)

                if _is_valid_solution(original, result):
                    tier_solved[tier] += 1
                    puzzle_bt.append(bt if bt is not None else 0)
                else:
                    puzzle_bt.append(BACKTRACK_CAP)
    except Exception:
        return _zero_metrics()

    num_total  = len(puzzle_bt)
    num_solved = sum(1 for bt in puzzle_bt if bt < BACKTRACK_CAP)
    avg_bt     = sum(puzzle_bt) / num_total if num_total else float(BACKTRACK_CAP)
    efficiency = 1.0 / (1.0 + avg_bt / SCALE)

    easy_rate   = tier_solved["easy"]   / tier_total["easy"]   if tier_total["easy"]   else 0.0
    hard_rate   = tier_solved["hard"]   / tier_total["hard"]   if tier_total["hard"]   else 0.0
    expert_rate = tier_solved["expert"] / tier_total["expert"] if tier_total["expert"] else 0.0
    solve_rate  = num_solved / num_total if num_total else 0.0

    return {
        "avg_bt":         avg_bt,
        "efficiency":     efficiency,
        "solve_rate":     solve_rate,
        "easy_rate":      easy_rate,
        "hard_rate":      hard_rate,
        "expert_rate":    expert_rate,
        "combined_score": efficiency,
    }


def _zero_metrics():
    return {
        "avg_bt":         float(BACKTRACK_CAP),
        "efficiency":     0.0,
        "solve_rate":     0.0,
        "easy_rate":      0.0,
        "hard_rate":      0.0,
        "expert_rate":    0.0,
        "combined_score": 0.0,
    }
