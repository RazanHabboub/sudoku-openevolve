def solve(grid, steps=None):
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]
    backtracks = 0

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
        nonlocal backtracks
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
                backtracks += 1
        return False

    result = grid if backtrack() else None
    return result, steps, backtracks
