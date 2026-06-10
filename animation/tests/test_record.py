import pytest

from animation.tests.conftest import TEST_PUZZLE, is_valid_solution
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
    import copy
    original = copy.deepcopy(TEST_PUZZLE)
    backtracking_record.solve(TEST_PUZZLE)
    assert TEST_PUZZLE == original

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
