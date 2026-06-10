# Sudoku Solver Animation — Design Spec

**Date:** 2026-06-10
**Project:** CS6501 OpenEvolve Sudoku Demo Video

## Overview

Generate 12 individual MP4 clips (4 solvers × 3 difficulty levels) plus 3 composed clips ready for the demo video. Clips show cells filling in and reverting in real time at a fixed visual speed, with a live backtrack counter. Faster solvers finish earlier and show a "SOLVED ✓" overlay while slower solvers are still running — making the performance gap viscerally clear without needing a manual video editor.

## File Structure

```
animation/
  solvers/
    backtracking_record.py    # baseline backtracking with step recording
    naked_singles_record.py   # baseline naked singles with step recording
    mrv_record.py             # baseline MRV with step recording
    best_record.py            # best evolved solver with step recording
  render.py                   # step log → matplotlib FuncAnimation → MP4
  compose.py                  # tile individual clips into composed demo clips
  make_clips.py               # top-level: pick puzzles, produce all clips
output/
  easy_backtracking.mp4
  easy_naked_singles.mp4
  easy_mrv.mp4
  easy_best.mp4
  hard_backtracking.mp4
  hard_naked_singles.mp4
  hard_mrv.mp4
  hard_best.mp4
  expert_backtracking.mp4
  expert_naked_singles.mp4
  expert_mrv.mp4
  expert_best.mp4
  easy_4up.mp4                # composed: 2×2 grid of all 4 solvers
  hard_2up.mp4                # composed: baseline vs best, side by side
  expert_2up.mp4              # composed: baseline vs best, side by side
```

Source solvers in `solvers/` and `results/best/` are untouched.

## Step Recording

Each `animation/solvers/*_record.py` is a copy of its solver with:

- `solve()` gains an optional `steps=None` parameter
- Every `grid[r][c] = val` is paired with `if steps is not None: steps.append((r, c, val))`
- `val == 0` means a revert (backtrack); positive val means a placement
- This applies to all grid writes, including propagation fills in the best solver
- `solve()` returns `(solved_grid_or_None, steps, final_backtracks)` as a tuple

Example (backtracking solver):

```python
def solve(grid, steps=None):
    ...
    def backtrack():
        ...
        grid[r][c] = num
        if steps is not None: steps.append((r, c, num))
        if backtrack(): return True
        grid[r][c] = 0
        if steps is not None: steps.append((r, c, 0))
        BACKTRACKS += 1
```

## Rendering (`render.py`)

**Function signature:**
```python
render_clip(initial_grid, steps, title, output_path, steps_per_frame, total_frames, fps=30)
```

`steps_per_frame` and `total_frames` are computed by `make_clips.py` (see below) so all clips within a difficulty share the same values.

**Visual layout:**
- 9×9 grid; thin lines between cells, thick lines between 3×3 boxes
- Given cells (pre-filled in puzzle): dark background, white number — fixed throughout
- Solver-placed cells: light background, colored number
- Empty cells: white
- Title (solver name) above the grid
- Backtrack counter below: `Backtracks: N`

**Speed:** Each frame advances `steps_per_frame` steps through the step log. Once all steps are exhausted the frame freezes on the solved grid and displays a **"SOLVED ✓"** overlay for the remaining frames.

**Output:** `FuncAnimation` saved via `writer='ffmpeg'` to MP4 at specified fps.

## Composition (`compose.py`)

Uses ffmpeg's `xstack` filter to tile individual clips:

- `easy_4up.mp4`: 2×2 grid layout of `easy_backtracking`, `easy_naked_singles`, `easy_mrv`, `easy_best`
- `hard_2up.mp4`: side-by-side `hard_backtracking` and `hard_best`
- `expert_2up.mp4`: side-by-side `expert_backtracking` and `expert_best`

Because all clips within a difficulty are the same duration (see below), `xstack` requires no padding.

## Puzzle Selection & `make_clips.py`

One puzzle is picked per difficulty level and reused for all 4 solvers, so comparisons within a difficulty are fair.

**Default selection:** The puzzle where baseline backtracking has the median backtrack count for that difficulty. Avoids outliers.

**Override:** `--easy-idx N --hard-idx N --expert-idx N` CLI flags for swapping in a better-looking puzzle after previewing.

**Speed control:** For each difficulty, `steps_per_frame` is fixed across all 4 solvers and set so the *slowest* solver (most steps) plays out in a target duration. All 4 clips then have the same `total_frames`; faster solvers hit their final state early and show "SOLVED ✓" for the remainder.

```
TARGET_SECONDS = {easy: 6, hard: 10, expert: 10}

for difficulty in [easy, hard, expert]:
    puzzle = pick_puzzle(difficulty)
    all_steps = {solver: run_recording_solver(solver, puzzle) for solver in solvers}
    max_steps = max(len(s.steps) for s in all_steps.values())
    steps_per_frame = max(1, ceil(max_steps / (TARGET_SECONDS[difficulty] * fps)))
    total_frames = ceil(max_steps / steps_per_frame)

    for solver, (solved, steps, bt) in all_steps.items():
        render_clip(puzzle, steps, solver_name,
                    output/difficulty_solver.mp4,
                    steps_per_frame, total_frames)

compose.py()  # produce the three composed clips
```

## Dependencies

- `matplotlib` (already in cs6501 env)
- `ffmpeg` (for MP4 export via matplotlib's ffmpeg writer and for `compose.py`)
- `pandas` (for reading `data/eval_puzzles.csv`)

Verify ffmpeg is available: `ffmpeg -version`. If not, install via `conda install -c conda-forge ffmpeg`.

## Intended Use in Demo Video

| Clip | Content | Purpose |
|------|---------|---------|
| `easy_4up.mp4` | All 4 solvers, easy puzzle | Establish comparison — all solve it, but at different speeds |
| `hard_2up.mp4` or `expert_2up.mp4` | Baseline vs best evolved | Deliver the payoff — dramatic contrast |
