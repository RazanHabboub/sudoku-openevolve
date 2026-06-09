def solve(grid):
    """
    Sudoku solver using naked-single propagation + MRV backtracking.
    Input: 9x9 grid where 0 means empty.
    Output: solved 9x9 grid, or None if no solution.
    """
    grid = [row[:] for row in grid]

    def candidates(r, c):
        used = set(grid[r])
        used.update(grid[i][c] for i in range(9))
        br, bc = (r // 3) * 3, (c // 3) * 3
        used.update(grid[br + dr][bc + dc] for dr in range(3) for dc in range(3))
        return set(range(1, 10)) - used

    def propagate():
        """Fill naked singles until none remain. Returns False on contradiction."""
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
                            grid[r][c] = next(iter(cands))
                            changed = True
        return True

    def backtrack():
        if not propagate():
            return False

        # MRV: branch on the empty cell with fewest candidates
        best_r = best_c = -1
        best_cands = None
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    cands = candidates(r, c)
                    if best_cands is None or len(cands) < len(best_cands):
                        best_r, best_c, best_cands = r, c, cands

        if best_r == -1:
            return True  # all cells filled

        saved = [row[:] for row in grid]
        for val in best_cands:
            grid[best_r][best_c] = val
            if backtrack():
                return True
            for i in range(9):
                grid[i][:] = saved[i]

        return False

    return grid if backtrack() else None
