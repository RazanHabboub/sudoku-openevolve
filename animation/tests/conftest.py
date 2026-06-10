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
