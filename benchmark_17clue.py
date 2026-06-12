"""
Benchmark all four solvers on a subset of the puzzles2_17_clue dataset.

Usage (from project root, cs6501 env):
    python benchmark_17clue.py                  # first 200 puzzles, 5s timeout
    python benchmark_17clue.py --n 500          # first 500 puzzles
    python benchmark_17clue.py --n 50 --timeout 10
    python benchmark_17clue.py --skip-slow      # skip baseline backtracking (very slow)
"""

import argparse
import importlib.util
import os
import sys
import threading
import time
import types
from queue import Empty, Queue
from statistics import median

DATASET = os.path.join(os.path.dirname(__file__), "data", "tdoku", "data", "puzzles2_17_clue")
BACKTRACK_CAP = 1_500_000

SOLVERS = [
    ("Backtracking",   "solvers/baseline_backtracking.py"),
    ("Naked Singles",  "solvers/baseline_naked_singles.py"),
    ("MRV",            "solvers/baseline_mrv.py"),
    ("Best Evolved",   "results/best/best_program.py"),
]


def load_solver(path):
    with open(path) as f:
        code = f.read()
    mod = types.ModuleType("solver")
    exec(compile(code, path, "exec"), mod.__dict__)
    return mod


def parse_puzzle(line):
    return [[0 if ch == '.' else int(ch) for ch in line[r*9:(r+1)*9]] for r in range(9)]


def is_valid(original, solved):
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
            if {solved[r][c] for r in range(br, br+3) for c in range(bc, bc+3)} != nums:
                return False
    return True


def solve_with_timeout(solve_fn, module, grid, timeout):
    q = Queue()

    def _run():
        t0 = time.perf_counter()
        try:
            result = solve_fn(grid)
            bt = getattr(module, "BACKTRACKS", 0)
            q.put((result, time.perf_counter() - t0, bt))
        except Exception as e:
            q.put((None, time.perf_counter() - t0, 0))

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    try:
        return q.get(timeout=timeout)
    except Empty:
        return None, timeout, None


def benchmark_solver(name, module, puzzles, timeout):
    solve_fn = module.solve
    bt_list = []
    time_list = []
    solved = 0

    for i, puzzle in enumerate(puzzles):
        result, elapsed, bt = solve_with_timeout(solve_fn, module, puzzle, timeout)
        if is_valid(puzzle, result):
            solved += 1
            bt_list.append(bt if bt is not None else 0)
        else:
            bt_list.append(BACKTRACK_CAP)
        time_list.append(elapsed)

        if (i + 1) % 50 == 0:
            print(f"    {name}: {i+1}/{len(puzzles)} puzzles done "
                  f"({solved} solved so far)...", flush=True)

    n = len(puzzles)
    solve_rate = solved / n
    avg_bt = sum(bt_list) / n
    solved_bt = [b for b in bt_list if b < BACKTRACK_CAP]
    med_bt = median(solved_bt) if solved_bt else float('nan')
    avg_time = sum(time_list) / n

    return {
        "solved": solved,
        "total": n,
        "solve_rate": solve_rate,
        "avg_bt_all": avg_bt,
        "median_bt_solved": med_bt,
        "avg_time_s": avg_time,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200,
                        help="Number of puzzles to test (default: 200)")
    parser.add_argument("--timeout", type=float, default=5.0,
                        help="Per-puzzle timeout in seconds (default: 5.0)")
    parser.add_argument("--skip-slow", action="store_true",
                        help="Skip baseline backtracking (very slow on 17-clue)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip first N puzzles in dataset")
    args = parser.parse_args()

    # Load puzzles
    puzzles = []
    with open(DATASET) as f:
        skipped = 0
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if skipped < args.offset:
                skipped += 1
                continue
            if len(line) == 81:
                puzzles.append(parse_puzzle(line))
            if len(puzzles) >= args.n:
                break

    print(f"\npuzzles2_17_clue benchmark")
    print(f"Puzzles: {len(puzzles)}  |  Timeout: {args.timeout}s  |  Offset: {args.offset}")
    print("=" * 70)

    results = {}
    for name, path in SOLVERS:
        if args.skip_slow and name == "Backtracking":
            print(f"\n[{name}] skipped (--skip-slow)")
            continue
        full_path = os.path.join(os.path.dirname(__file__), path)
        module = load_solver(full_path)
        print(f"\n[{name}]")
        r = benchmark_solver(name, module, puzzles, args.timeout)
        results[name] = r

    # Summary table
    print("\n" + "=" * 70)
    print(f"{'Solver':<20} {'Solved':>8} {'SolveRate':>10} {'AvgBT(all)':>12} {'MedianBT':>10} {'AvgTime':>9}")
    print("-" * 70)
    for name, _ in SOLVERS:
        if name not in results:
            print(f"{name:<20} {'(skipped)':>8}")
            continue
        r = results[name]
        print(f"{name:<20} {r['solved']:>4}/{r['total']:<4} "
              f"{r['solve_rate']:>9.1%} "
              f"{r['avg_bt_all']:>12,.0f} "
              f"{r['median_bt_solved']:>10,.0f} "
              f"{r['avg_time_s']:>8.3f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
