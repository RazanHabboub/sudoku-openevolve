BACKTRACKS = 0  # reset to 0 at start of each solve(); increment on each undo

def solve(grid):
    """
    Baseline Sudoku solver using simple backtracking.
    Input: 9x9 grid where 0 means empty.
    Output: solved 9x9 grid, or None if no solution.
    """
    global BACKTRACKS
    BACKTRACKS = 0
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
                if backtrack():
                    return True
                grid[r][c] = 0
                BACKTRACKS += 1
        return False

    if backtrack():
        return grid
    return None
