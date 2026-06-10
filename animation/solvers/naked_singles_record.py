def solve(grid, steps=None):
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]
    backtracks = 0

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
        nonlocal backtracks
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
            for i in range(9):
                for j in range(9):
                    if grid[i][j] != saved[i][j]:
                        grid[i][j] = saved[i][j]
                        steps.append((i, j, saved[i][j]))
            backtracks += 1

        return False

    result = grid if backtrack() else None
    return result, steps, backtracks
