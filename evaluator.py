import csv
import time
from solvers import baseline_backtracking, baseline_mrv


def puzzle_to_grid(puzzle):
    return [[int(puzzle[r * 9 + c]) for c in range(9)] for r in range(9)]


def is_valid_solution(original, solved):
    if solved is None:
        return False

    nums = set(range(1, 10))

    # Preserve original clues
    for r in range(9):
        for c in range(9):
            if original[r][c] != 0 and original[r][c] != solved[r][c]:
                return False

    # Check rows and columns
    for i in range(9):
        if set(solved[i]) != nums:
            return False
        if set(solved[r][i] for r in range(9)) != nums:
            return False

    # Check 3x3 boxes
    for box_r in range(0, 9, 3):
        for box_c in range(0, 9, 3):
            box = []
            for r in range(box_r, box_r + 3):
                for c in range(box_c, box_c + 3):
                    box.append(solved[r][c])
            if set(box) != nums:
                return False

    return True


def evaluate_solver(name, solver_func, csv_path="data/puzzles_sample.csv"):
    solved_count = 0
    total_time = 0
    total = 0

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total += 1
            original = puzzle_to_grid(row["puzzle"])

            start = time.perf_counter()
            solved = solver_func(original)
            elapsed = time.perf_counter() - start

            total_time += elapsed

            if is_valid_solution(original, solved):
                solved_count += 1

    return {
        "solver": name,
        "total_puzzles": total,
        "solved": solved_count,
        "solve_rate": solved_count / total if total else 0,
        "total_time": total_time,
        "avg_time": total_time / total if total else 0,
    }


if __name__ == "__main__":
    solvers = [
        ("baseline_backtracking", baseline_backtracking.solve),
        ("baseline_mrv", baseline_mrv.solve),
    ]

    for name, func in solvers:
        result = evaluate_solver(name, func)
        print(result)