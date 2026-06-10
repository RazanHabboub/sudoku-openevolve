def solve(grid, steps=None):
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]
    backtracks = 0

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
        nonlocal backtracks
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
            backtracks += 1
        return False

    result = grid if backtrack() else None
    return result, steps, backtracks
