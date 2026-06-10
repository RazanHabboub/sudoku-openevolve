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
