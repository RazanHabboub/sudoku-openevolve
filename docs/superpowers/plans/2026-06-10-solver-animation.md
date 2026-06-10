# Solver Animation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate 12 individual MP4 clips + 3 composed demo clips showing each Sudoku solver (backtracking, naked singles, MRV, best evolved) solving easy/hard/expert puzzles, with cells filling/reverting in real time and a live backtrack counter.

**Architecture:** Each baseline solver is copied into `animation/solvers/` with a `steps` list parameter added — every `grid[r][c] = val` also appends `(r, c, val)` to the list. `render.py` replays those steps via matplotlib FuncAnimation at a fixed visual speed (same `steps_per_frame` across all solvers in a difficulty), holding the solved state with a "SOLVED ✓" overlay once finished. `compose.py` tiles individual clips into ready-to-use demo clips using ffmpeg's `xstack`/`hstack` filters.

**Tech Stack:** Python 3.13, matplotlib, ffmpeg, pandas, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `animation/__init__.py` | Create | Package marker |
| `animation/solvers/__init__.py` | Create | Package marker |
| `animation/solvers/backtracking_record.py` | Create | Baseline backtracking + step recording |
| `animation/solvers/mrv_record.py` | Create | Baseline MRV + step recording + BACKTRACKS counter |
| `animation/solvers/naked_singles_record.py` | Create | Baseline naked singles + step recording |
| `animation/solvers/best_record.py` | Create | Best evolved solver + step recording |
| `animation/render.py` | Create | Step log → matplotlib FuncAnimation → MP4 |
| `animation/compose.py` | Create | ffmpeg xstack/hstack composition |
| `animation/make_clips.py` | Create | Top-level orchestration: pick puzzles, produce all 15 clips |
| `animation/tests/__init__.py` | Create | Package marker |
| `animation/tests/conftest.py` | Create | Shared fixtures + sys.path setup |
| `animation/tests/test_record.py` | Create | Tests for all four recording solvers |
| `animation/tests/test_render.py` | Create | Smoke test for render_clip output |
| `output/` | Generated | MP4 output files (not committed) |

---

## Task 1: Directory scaffolding + ffmpeg check

**Files:**
- Create: `animation/__init__.py`
- Create: `animation/solvers/__init__.py`
- Create: `animation/tests/__init__.py`
- Create: `animation/tests/conftest.py`

- [ ] **Step 1: Create directories and package markers**

Run in PowerShell from `C:\Users\annaj\sudoku-openevolve`:

```powershell
New-Item -ItemType Directory -Force animation\solvers
New-Item -ItemType Directory -Force animation\tests
New-Item -ItemType File -Force animation\__init__.py
New-Item -ItemType File -Force animation\solvers\__init__.py
New-Item -ItemType File -Force animation\tests\__init__.py
```

- [ ] **Step 2: Write conftest.py**

Create `animation/tests/conftest.py`:

```python
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

TEST_PUZZLE = [
    [5,3,0, 0,7,0, 0,0,0],
    [6,0,0, 1,9,5, 0,0,0],
    [0,9,8, 0,0,0, 0,6,0],
    [8,0,0, 0,6,0, 0,0,3],
    [4,0,0, 8,0,3, 0,0,1],
    [7,0,0, 0,2,0, 0,0,6],
    [0,6,0, 0,0,0, 2,8,0],
    [0,0,0, 4,1,9, 0,0,5],
    [0,0,0, 0,8,0, 0,7,9],
]

TEST_SOLUTION = [
    [5,3,4, 6,7,8, 9,1,2],
    [6,7,2, 1,9,5, 3,4,8],
    [1,9,8, 3,4,2, 5,6,7],
    [8,5,9, 7,6,1, 4,2,3],
    [4,2,6, 8,5,3, 7,9,1],
    [7,1,3, 9,2,4, 8,5,6],
    [9,6,1, 5,3,7, 2,8,4],
    [2,8,7, 4,1,9, 6,3,5],
    [3,4,5, 2,8,6, 1,7,9],
]

def is_valid_solution(grid, original):
    for r in range(9):
        if set(grid[r]) != set(range(1, 10)):
            return False
    for c in range(9):
        if set(grid[r][c] for r in range(9)) != set(range(1, 10)):
            return False
    for br in range(3):
        for bc in range(3):
            box = [grid[br*3+r][bc*3+c] for r in range(3) for c in range(3)]
            if set(box) != set(range(1, 10)):
                return False
    for r in range(9):
        for c in range(9):
            if original[r][c] != 0 and grid[r][c] != original[r][c]:
                return False
    return True
```

- [ ] **Step 3: Verify ffmpeg is available**

Run:
```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -c "import matplotlib; print(matplotlib.__version__)"
ffmpeg -version
```

Expected: matplotlib version printed; ffmpeg version line printed.
If ffmpeg is missing, install it:
```bash
C:\Users\annaj\miniconda3\Scripts\conda.exe install -c conda-forge ffmpeg -n cs6501 -y
```

- [ ] **Step 4: Commit scaffolding**

```bash
cd C:\Users\annaj\sudoku-openevolve
git add animation/
git commit -m "feat: scaffold animation package"
```

---

## Task 2: `backtracking_record.py`

**Files:**
- Create: `animation/solvers/backtracking_record.py`
- Create: `animation/tests/test_record.py` (partial — add more in later tasks)

Source: copy of `solvers/baseline_backtracking.py` with step recording added.

- [ ] **Step 1: Write the failing test**

Create `animation/tests/test_record.py`:

```python
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from animation.tests.conftest import TEST_PUZZLE, TEST_SOLUTION, is_valid_solution
from animation.solvers import backtracking_record

def test_bt_solves_correctly():
    grid, steps, bt = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    assert grid is not None
    assert is_valid_solution(grid, TEST_PUZZLE)

def test_bt_returns_tuple():
    result = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    assert isinstance(result, tuple) and len(result) == 3

def test_bt_steps_nonempty():
    _, steps, _ = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    assert len(steps) > 0

def test_bt_steps_valid_coords():
    _, steps, _ = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    for r, c, v in steps:
        assert 0 <= r <= 8
        assert 0 <= c <= 8
        assert 0 <= v <= 9

def test_bt_steps_skip_given_cells():
    _, steps, _ = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    given = {(r, c) for r in range(9) for c in range(9) if TEST_PUZZLE[r][c] != 0}
    for r, c, _ in steps:
        assert (r, c) not in given

def test_bt_backtracks_matches_revert_count():
    _, steps, bt = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    revert_count = sum(1 for _, _, v in steps if v == 0)
    assert bt == revert_count

def test_bt_does_not_mutate_input():
    original = [row[:] for row in TEST_PUZZLE]
    backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    assert TEST_PUZZLE == original
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:\Users\annaj\sudoku-openevolve
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py::test_bt_returns_tuple -v
```

Expected: `ModuleNotFoundError` or `ImportError` — `backtracking_record` does not exist yet.

- [ ] **Step 3: Write `backtracking_record.py`**

Create `animation/solvers/backtracking_record.py`:

```python
BACKTRACKS = 0

def solve(grid, steps=None):
    global BACKTRACKS
    BACKTRACKS = 0
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]

    def find_empty():
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    return r, c
        return None

    def is_valid(r, c, num):
        if num in grid[r]:
            return False
        for i in range(9):
            if grid[i][c] == num:
                return False
        box_r = (r // 3) * 3
        box_c = (c // 3) * 3
        for i in range(box_r, box_r + 3):
            for j in range(box_c, box_c + 3):
                if grid[i][j] == num:
                    return False
        return True

    def backtrack():
        global BACKTRACKS
        empty = find_empty()
        if empty is None:
            return True
        r, c = empty
        for num in range(1, 10):
            if is_valid(r, c, num):
                grid[r][c] = num
                steps.append((r, c, num))
                if backtrack():
                    return True
                grid[r][c] = 0
                steps.append((r, c, 0))
                BACKTRACKS += 1
        return False

    result = grid if backtrack() else None
    return result, steps, BACKTRACKS
```

- [ ] **Step 4: Run all backtracking tests**

```bash
cd C:\Users\annaj\sudoku-openevolve
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "bt" -v
```

Expected: all 7 `test_bt_*` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add animation/solvers/backtracking_record.py animation/tests/test_record.py
git commit -m "feat: add backtracking recording solver"
```

---

## Task 3: `mrv_record.py`

**Files:**
- Create: `animation/solvers/mrv_record.py`
- Modify: `animation/tests/test_record.py` (append MRV tests)

Source: copy of `solvers/baseline_mrv.py`. Note: the original has **no BACKTRACKS counter** — add one here.

- [ ] **Step 1: Append MRV tests to `test_record.py`**

Append to `animation/tests/test_record.py`:

```python
from animation.solvers import mrv_record

def test_mrv_solves_correctly():
    grid, steps, bt = mrv_record.solve([row[:] for row in TEST_PUZZLE])
    assert grid is not None
    assert is_valid_solution(grid, TEST_PUZZLE)

def test_mrv_returns_tuple():
    result = mrv_record.solve([row[:] for row in TEST_PUZZLE])
    assert isinstance(result, tuple) and len(result) == 3

def test_mrv_steps_nonempty():
    _, steps, _ = mrv_record.solve([row[:] for row in TEST_PUZZLE])
    assert len(steps) > 0

def test_mrv_steps_valid_coords():
    _, steps, _ = mrv_record.solve([row[:] for row in TEST_PUZZLE])
    for r, c, v in steps:
        assert 0 <= r <= 8
        assert 0 <= c <= 8
        assert 0 <= v <= 9

def test_mrv_backtracks_matches_revert_count():
    _, steps, bt = mrv_record.solve([row[:] for row in TEST_PUZZLE])
    revert_count = sum(1 for _, _, v in steps if v == 0)
    assert bt == revert_count
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "mrv" -v
```

Expected: `ImportError` — `mrv_record` does not exist yet.

- [ ] **Step 3: Write `mrv_record.py`**

Create `animation/solvers/mrv_record.py`:

```python
BACKTRACKS = 0

def solve(grid, steps=None):
    global BACKTRACKS
    BACKTRACKS = 0
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]

    def valid_numbers(r, c):
        nums = set(range(1, 10))
        nums -= set(grid[r])
        nums -= {grid[i][c] for i in range(9)}
        box_r = (r // 3) * 3
        box_c = (c // 3) * 3
        nums -= {grid[i][j] for i in range(box_r, box_r + 3) for j in range(box_c, box_c + 3)}
        return nums

    def find_best_empty():
        best_cell = None
        best_options = None
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    options = valid_numbers(r, c)
                    if best_options is None or len(options) < len(best_options):
                        best_cell = (r, c)
                        best_options = options
        return best_cell, best_options

    def backtrack():
        global BACKTRACKS
        cell, options = find_best_empty()
        if cell is None:
            return True
        if not options:
            return False
        r, c = cell
        for num in sorted(options):
            grid[r][c] = num
            steps.append((r, c, num))
            if backtrack():
                return True
            grid[r][c] = 0
            steps.append((r, c, 0))
            BACKTRACKS += 1
        return False

    result = grid if backtrack() else None
    return result, steps, BACKTRACKS
```

- [ ] **Step 4: Run MRV tests**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "mrv" -v
```

Expected: all 5 `test_mrv_*` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add animation/solvers/mrv_record.py animation/tests/test_record.py
git commit -m "feat: add MRV recording solver"
```

---

## Task 4: `naked_singles_record.py`

**Files:**
- Create: `animation/solvers/naked_singles_record.py`
- Modify: `animation/tests/test_record.py` (append naked singles tests)

Source: copy of `solvers/baseline_naked_singles.py`. The restore logic uses `grid[i][:] = saved[i]` (full row slice assignment) — replace with cell-by-cell to capture individual reverts.

- [ ] **Step 1: Append naked singles tests to `test_record.py`**

Append to `animation/tests/test_record.py`:

```python
from animation.solvers import naked_singles_record

def test_ns_solves_correctly():
    grid, steps, bt = naked_singles_record.solve([row[:] for row in TEST_PUZZLE])
    assert grid is not None
    assert is_valid_solution(grid, TEST_PUZZLE)

def test_ns_returns_tuple():
    result = naked_singles_record.solve([row[:] for row in TEST_PUZZLE])
    assert isinstance(result, tuple) and len(result) == 3

def test_ns_steps_nonempty():
    _, steps, _ = naked_singles_record.solve([row[:] for row in TEST_PUZZLE])
    assert len(steps) > 0

def test_ns_steps_valid_coords():
    _, steps, _ = naked_singles_record.solve([row[:] for row in TEST_PUZZLE])
    for r, c, v in steps:
        assert 0 <= r <= 8
        assert 0 <= c <= 8
        assert 0 <= v <= 9

def test_ns_bt_count_positive_or_zero():
    _, _, bt = naked_singles_record.solve([row[:] for row in TEST_PUZZLE])
    assert bt >= 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "ns" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Write `naked_singles_record.py`**

Create `animation/solvers/naked_singles_record.py`:

```python
BACKTRACKS = 0

def solve(grid, steps=None):
    global BACKTRACKS
    BACKTRACKS = 0
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]

    def candidates(r, c):
        used = set(grid[r])
        used.update(grid[i][c] for i in range(9))
        br, bc = (r // 3) * 3, (c // 3) * 3
        used.update(grid[br + dr][bc + dc] for dr in range(3) for dc in range(3))
        return set(range(1, 10)) - used

    def propagate():
        changed = True
        while changed:
            changed = False
            for r in range(9):
                for c in range(9):
                    if grid[r][c] == 0:
                        cands = candidates(r, c)
                        if not cands:
                            return False
                        if len(cands) == 1:
                            val = next(iter(cands))
                            grid[r][c] = val
                            steps.append((r, c, val))
                            changed = True
        return True

    def backtrack():
        global BACKTRACKS
        if not propagate():
            return False

        best_r = best_c = -1
        best_cands = None
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    cands = candidates(r, c)
                    if best_cands is None or len(cands) < len(best_cands):
                        best_r, best_c, best_cands = r, c, cands

        if best_r == -1:
            return True

        saved = [row[:] for row in grid]
        for val in best_cands:
            grid[best_r][best_c] = val
            steps.append((best_r, best_c, val))
            if backtrack():
                return True
            # Restore cell by cell so each revert is recorded
            for i in range(9):
                for j in range(9):
                    if grid[i][j] != saved[i][j]:
                        grid[i][j] = saved[i][j]
                        steps.append((i, j, saved[i][j]))
            BACKTRACKS += 1

        return False

    result = grid if backtrack() else None
    return result, steps, BACKTRACKS
```

- [ ] **Step 4: Run naked singles tests**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "ns" -v
```

Expected: all 5 `test_ns_*` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add animation/solvers/naked_singles_record.py animation/tests/test_record.py
git commit -m "feat: add naked singles recording solver"
```

---

## Task 5: `best_record.py`

**Files:**
- Create: `animation/solvers/best_record.py`
- Modify: `animation/tests/test_record.py` (append best solver tests)

Source: copy of `results/best/best_program.py`. Grid writes occur in both `_propagate_constraints` (naked/hidden singles) and `backtrack` — all must be recorded. `steps` is captured from the enclosing `solve()` scope.

- [ ] **Step 1: Append best solver tests to `test_record.py`**

Append to `animation/tests/test_record.py`:

```python
from animation.solvers import best_record

def test_best_solves_correctly():
    grid, steps, bt = best_record.solve([row[:] for row in TEST_PUZZLE])
    assert grid is not None
    assert is_valid_solution(grid, TEST_PUZZLE)

def test_best_returns_tuple():
    result = best_record.solve([row[:] for row in TEST_PUZZLE])
    assert isinstance(result, tuple) and len(result) == 3

def test_best_steps_nonempty():
    _, steps, _ = best_record.solve([row[:] for row in TEST_PUZZLE])
    assert len(steps) > 0

def test_best_steps_valid_coords():
    _, steps, _ = best_record.solve([row[:] for row in TEST_PUZZLE])
    for r, c, v in steps:
        assert 0 <= r <= 8
        assert 0 <= c <= 8
        assert 0 <= v <= 9

def test_best_fewer_backtracks_than_baseline():
    _, _, bt_best = best_record.solve([row[:] for row in TEST_PUZZLE])
    _, _, bt_bt = backtracking_record.solve([row[:] for row in TEST_PUZZLE])
    assert bt_best <= bt_bt
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "best" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Write `best_record.py`**

Create `animation/solvers/best_record.py`:

```python
BACKTRACKS = 0

def solve(grid, steps=None):
    global BACKTRACKS
    BACKTRACKS = 0
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]

    candidates = {}
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                candidates[(r, c)] = set(range(1, 10))

    def _get_peers(r, c):
        peers = set()
        for col in range(9):
            if col != c: peers.add((r, col))
        for row in range(9):
            if row != r: peers.add((row, c))
        box_r, box_c = (r // 3) * 3, (c // 3) * 3
        for i in range(box_r, box_r + 3):
            for j in range(box_c, box_c + 3):
                if (i, j) != (r, c): peers.add((i, j))
        return peers

    def _update_candidates_on_placement(r, c, num, current_candidates):
        if (r, c) in current_candidates:
            del current_candidates[(r, c)]
        for pr, pc in _get_peers(r, c):
            if (pr, pc) in current_candidates and num in current_candidates[(pr, pc)]:
                current_candidates[(pr, pc)].remove(num)
                if not current_candidates[(pr, pc)]:
                    return False
        return True

    def _propagate_constraints(current_candidates):
        while True:
            changed = False
            cells_to_remove = []
            for (r, c), possible_values in list(current_candidates.items()):
                if len(possible_values) == 1:
                    num = list(possible_values)[0]
                    grid[r][c] = num
                    steps.append((r, c, num))
                    if not _update_candidates_on_placement(r, c, num, current_candidates):
                        return False
                    cells_to_remove.append((r, c))
                    changed = True
            for r, c in cells_to_remove:
                if (r, c) in current_candidates:
                    del current_candidates[(r, c)]
            if changed:
                continue
            for unit_type in range(3):
                for i in range(9):
                    num_positions = {num: [] for num in range(1, 10)}
                    if unit_type == 0:
                        unit_cells_coords = [(i, c) for c in range(9)]
                    elif unit_type == 1:
                        unit_cells_coords = [(r, i) for r in range(9)]
                    else:
                        box_r, box_c = (i // 3) * 3, (i % 3) * 3
                        unit_cells_coords = [(r, c) for r in range(box_r, box_r + 3) for c in range(box_c, box_c + 3)]
                    for r, c in unit_cells_coords:
                        if (r, c) in current_candidates:
                            for num in current_candidates[(r, c)]:
                                num_positions[num].append((r, c))
                    for num, cells_with_num in num_positions.items():
                        if len(cells_with_num) == 1:
                            r, c = cells_with_num[0]
                            if (r, c) in current_candidates and len(current_candidates[(r, c)]) > 1:
                                grid[r][c] = num
                                steps.append((r, c, num))
                                current_candidates[(r, c)] = {num}
                                if not _update_candidates_on_placement(r, c, num, current_candidates):
                                    return False
                                changed = True
            if not changed:
                break
        return True

    def backtrack(current_candidates):
        global BACKTRACKS
        if not _propagate_constraints(current_candidates):
            return False
        if not current_candidates:
            return True
        r, c = min(current_candidates, key=lambda k: len(current_candidates[k]))
        original_cell_candidates = current_candidates[(r, c)].copy()
        for num in sorted(list(original_cell_candidates)):
            grid[r][c] = num
            steps.append((r, c, num))
            temp_candidates_state = {k: v.copy() for k, v in current_candidates.items()}
            if _update_candidates_on_placement(r, c, num, current_candidates):
                if backtrack(current_candidates):
                    return True
            grid[r][c] = 0
            steps.append((r, c, 0))
            BACKTRACKS += 1
            current_candidates = temp_candidates_state
        return False

    initial_candidates = {}
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                initial_candidates[(r, c)] = set(range(1, 10))
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                num = grid[r][c]
                if not _update_candidates_on_placement(r, c, num, initial_candidates):
                    return None, steps, BACKTRACKS

    result = grid if backtrack(initial_candidates) else None
    return result, steps, BACKTRACKS
```

- [ ] **Step 4: Run best solver tests**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -k "best" -v
```

Expected: all 5 `test_best_*` tests PASS.

- [ ] **Step 5: Run all recording solver tests**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_record.py -v
```

Expected: all 22 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add animation/solvers/best_record.py animation/tests/test_record.py
git commit -m "feat: add best evolved solver recording"
```

---

## Task 6: `render.py`

**Files:**
- Create: `animation/render.py`
- Create: `animation/tests/test_render.py`

- [ ] **Step 1: Write the smoke test**

Create `animation/tests/test_render.py`:

```python
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from animation.tests.conftest import TEST_PUZZLE
from animation.solvers.backtracking_record import solve
from animation.render import render_clip

@pytest.mark.skipif(
    __import__('shutil').which('ffmpeg') is None,
    reason="ffmpeg not available"
)
def test_render_creates_mp4():
    _, steps, _ = solve([row[:] for row in TEST_PUZZLE])
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "test.mp4")
        render_clip(TEST_PUZZLE, steps, "Test Solver", out,
                    steps_per_frame=max(1, len(steps) // 30),
                    total_frames=30, fps=10)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 1000
```

- [ ] **Step 2: Run test to verify it fails**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_render.py -v
```

Expected: `ImportError` — `render` module does not exist yet.

- [ ] **Step 3: Write `render.py`**

Create `animation/render.py`:

```python
import os
from math import ceil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation


def render_clip(initial_grid, steps, title, output_path, steps_per_frame, total_frames, fps=30):
    fig, ax = plt.subplots(figsize=(4.5, 5.5))
    fig.patch.set_facecolor('white')
    ax.set_xlim(0, 9)
    ax.set_ylim(-1, 9)
    ax.set_aspect('equal')
    ax.axis('off')

    # Grid lines
    for i in range(10):
        lw = 2.5 if i % 3 == 0 else 0.5
        ax.plot([i, i], [0, 9], 'k-', lw=lw, zorder=2)
        ax.plot([0, 9], [i, i], 'k-', lw=lw, zorder=2)

    given = {(r, c) for r in range(9) for c in range(9) if initial_grid[r][c] != 0}
    current = [row[:] for row in initial_grid]

    # Background patches for given cells
    for r, c in given:
        rect = patches.Rectangle((c, 8 - r), 1, 1, facecolor='#E8E8E8', edgecolor='none', zorder=1)
        ax.add_patch(rect)

    # Cell text objects
    cell_texts = {}
    for r in range(9):
        for c in range(9):
            val = initial_grid[r][c]
            color = '#222222' if (r, c) in given else '#1565C0'
            weight = 'bold' if (r, c) in given else 'normal'
            txt = ax.text(c + 0.5, 8 - r + 0.5,
                          str(val) if val != 0 else '',
                          ha='center', va='center', fontsize=14,
                          color=color, fontweight=weight, zorder=3)
            cell_texts[(r, c)] = txt

    ax.set_title(title, fontsize=12, pad=8, fontweight='bold')
    bt_text = ax.text(4.5, -0.6, 'Backtracks: 0',
                      ha='center', va='top', fontsize=11, color='#333333')
    solved_text = ax.text(4.5, 4.5, 'SOLVED ✓',
                          ha='center', va='center', fontsize=26,
                          color='#2E7D32', fontweight='bold', alpha=0.88,
                          visible=False, zorder=5)

    state = {'step_idx': 0, 'bt': 0}
    solved_at_frame = ceil(len(steps) / steps_per_frame) if steps else 0

    def update(frame):
        end_step = min((frame + 1) * steps_per_frame, len(steps))
        while state['step_idx'] < end_step:
            r, c, v = steps[state['step_idx']]
            current[r][c] = v
            if v == 0:
                state['bt'] += 1
            state['step_idx'] += 1

        for r in range(9):
            for c in range(9):
                if (r, c) not in given:
                    val = current[r][c]
                    cell_texts[(r, c)].set_text(str(val) if val != 0 else '')

        bt_text.set_text(f'Backtracks: {state["bt"]}')

        if frame >= solved_at_frame:
            solved_text.set_visible(True)

        return list(cell_texts.values()) + [bt_text, solved_text]

    anim = FuncAnimation(fig, update, frames=total_frames,
                         interval=1000 / fps, blit=False)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    anim.save(output_path, writer='ffmpeg', fps=fps, dpi=100,
              extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p'])
    plt.close(fig)
```

- [ ] **Step 4: Run the smoke test**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/test_render.py -v -s
```

Expected: `test_render_creates_mp4` PASS. This may take 20–30 seconds (renders 30 frames at 10fps).

- [ ] **Step 5: Commit**

```bash
git add animation/render.py animation/tests/test_render.py
git commit -m "feat: add matplotlib animation renderer"
```

---

## Task 7: `compose.py`

**Files:**
- Create: `animation/compose.py`

No automated tests — this is a thin subprocess wrapper around ffmpeg; correctness is verified in the end-to-end run (Task 9).

- [ ] **Step 1: Write `compose.py`**

Create `animation/compose.py`:

```python
import subprocess


def compose_4up(clips, output_path):
    """Tile four clips in a 2x2 grid. All clips must have the same duration."""
    a, b, c, d = clips
    cmd = [
        'ffmpeg', '-y',
        '-i', a, '-i', b, '-i', c, '-i', d,
        '-filter_complex',
        '[0:v][1:v][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]',
        '-map', '[v]',
        '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
        output_path,
    ]
    subprocess.run(cmd, check=True)


def compose_2up(clip1, clip2, output_path):
    """Place two clips side by side. Both clips must have the same duration."""
    cmd = [
        'ffmpeg', '-y',
        '-i', clip1, '-i', clip2,
        '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]',
        '-map', '[v]',
        '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
        output_path,
    ]
    subprocess.run(cmd, check=True)
```

- [ ] **Step 2: Commit**

```bash
git add animation/compose.py
git commit -m "feat: add ffmpeg clip composition helpers"
```

---

## Task 8: `make_clips.py`

**Files:**
- Create: `animation/make_clips.py`

- [ ] **Step 1: Write `make_clips.py`**

Create `animation/make_clips.py`:

```python
#!/usr/bin/env python3
import argparse
import os
import sys
from math import ceil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from animation.solvers.backtracking_record import solve as bt_solve
from animation.solvers.mrv_record import solve as mrv_solve
from animation.solvers.naked_singles_record import solve as ns_solve
from animation.solvers.best_record import solve as best_solve
from animation.render import render_clip
from animation.compose import compose_4up, compose_2up

SOLVERS = [
    ('backtracking', bt_solve, 'Backtracking'),
    ('naked_singles', ns_solve, 'Naked Singles'),
    ('mrv', mrv_solve, 'MRV'),
    ('best', best_solve, 'Best Evolved'),
]

TARGET_SECONDS = {'easy': 6, 'hard': 10, 'expert': 10}
FPS = 30
OUTPUT_DIR = 'output'


def parse_puzzle(s):
    return [[int(s[r * 9 + c]) for c in range(9)] for r in range(9)]


def pick_puzzle(df, difficulty, override_idx=None):
    subset = df[df['difficulty'] == difficulty].reset_index(drop=True)
    if override_idx is not None:
        return parse_puzzle(subset.iloc[override_idx]['puzzle'])
    bt_counts = []
    for _, row in subset.iterrows():
        grid = parse_puzzle(row['puzzle'])
        _, _, bt = bt_solve(grid)
        bt_counts.append(bt)
    median_idx = sorted(range(len(bt_counts)), key=lambda i: bt_counts[i])[len(bt_counts) // 2]
    print(f"  [{difficulty}] selected puzzle index {median_idx} "
          f"(baseline bt={bt_counts[median_idx]})")
    return parse_puzzle(subset.iloc[median_idx]['puzzle'])


def main():
    parser = argparse.ArgumentParser(description='Generate Sudoku solver animation clips')
    parser.add_argument('--easy-idx', type=int, help='Puzzle index override for easy difficulty')
    parser.add_argument('--hard-idx', type=int, help='Puzzle index override for hard difficulty')
    parser.add_argument('--expert-idx', type=int, help='Puzzle index override for expert difficulty')
    parser.add_argument('--fps', type=int, default=FPS)
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.read_csv('data/eval_puzzles.csv')

    idx_overrides = {
        'easy': args.easy_idx,
        'hard': args.hard_idx,
        'expert': args.expert_idx,
    }

    composed_clips = {}

    for difficulty in ['easy', 'hard', 'expert']:
        print(f'\n=== {difficulty.upper()} ===')
        puzzle = pick_puzzle(df, difficulty, idx_overrides.get(difficulty))

        # Run all solvers and collect steps
        solver_results = {}
        for key, solve_fn, label in SOLVERS:
            _, steps, bt = solve_fn([row[:] for row in puzzle])
            solver_results[key] = (steps, bt, label)
            print(f'  {label}: {len(steps)} steps, {bt} backtracks')

        max_steps = max(len(v[0]) for v in solver_results.values())
        if max_steps == 0:
            max_steps = 1
        target_secs = TARGET_SECONDS[difficulty]
        steps_per_frame = max(1, ceil(max_steps / (target_secs * args.fps)))
        total_frames = ceil(max_steps / steps_per_frame)
        print(f'  steps_per_frame={steps_per_frame}, total_frames={total_frames}')

        clips = {}
        for key, solve_fn, label in SOLVERS:
            steps, bt, _ = solver_results[key]
            out = os.path.join(OUTPUT_DIR, f'{difficulty}_{key}.mp4')
            print(f'  Rendering {out} ...')
            render_clip(puzzle, steps, label, out, steps_per_frame, total_frames, args.fps)
            clips[key] = out

        composed_clips[difficulty] = clips

    # Composed clips
    print('\n=== Composing ===')

    easy = composed_clips['easy']
    easy_4up = os.path.join(OUTPUT_DIR, 'easy_4up.mp4')
    compose_4up(
        [easy['backtracking'], easy['naked_singles'], easy['mrv'], easy['best']],
        easy_4up,
    )
    print(f'  {easy_4up}')

    for diff in ['hard', 'expert']:
        clips = composed_clips[diff]
        out = os.path.join(OUTPUT_DIR, f'{diff}_2up.mp4')
        compose_2up(clips['backtracking'], clips['best'], out)
        print(f'  {out}')

    print('\nDone! Output clips:')
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.mp4'):
            size_kb = os.path.getsize(os.path.join(OUTPUT_DIR, f)) // 1024
            print(f'  {f}  ({size_kb} KB)')


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add animation/make_clips.py
git commit -m "feat: add make_clips orchestration script"
```

---

## Task 9: End-to-end run

- [ ] **Step 1: Run full test suite**

```bash
cd C:\Users\annaj\sudoku-openevolve
C:\Users\annaj\miniconda3\envs\cs6501\python.exe -m pytest animation/tests/ -v
```

Expected: all tests PASS (22 record tests + 1 render smoke test).

- [ ] **Step 2: Dry run on easy only to validate output**

```bash
cd C:\Users\annaj\sudoku-openevolve
C:\Users\annaj\miniconda3\envs\cs6501\python.exe animation/make_clips.py --easy-idx 0 --hard-idx 0 --expert-idx 0
```

This uses index 0 for all difficulties (skips median search) for a fast first run. Expected: 15 MP4 files in `output/`, no errors.

- [ ] **Step 3: Verify output files exist and are non-trivial**

```bash
Get-ChildItem output\*.mp4 | Select-Object Name, @{N='KB';E={[int]($_.Length/1024)}}
```

Expected: 15 files, each > 50 KB.

- [ ] **Step 4: Run full production run with median puzzle selection**

```bash
C:\Users\annaj\miniconda3\envs\cs6501\python.exe animation/make_clips.py
```

This searches for the median-backtrack puzzle per difficulty. May take 5–10 minutes total (easy puzzle search runs baseline on 100 puzzles; rendering hard/expert baseline clips with many steps is the bottleneck).

- [ ] **Step 5: Add `output/` to `.gitignore`**

Append to `.gitignore` (create if it doesn't exist):
```
output/
```

```bash
git add .gitignore
git commit -m "chore: gitignore output/ directory"
```

- [ ] **Step 6: Final commit**

```bash
git add animation/
git status
git commit -m "feat: complete solver animation pipeline"
```
