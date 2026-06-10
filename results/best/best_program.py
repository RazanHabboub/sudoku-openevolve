BACKTRACKS = 0

def solve(grid: list[list[int]]) -> list[list[int]] | None:
    """
    Solves a Sudoku puzzle using backtracking with constraint propagation.
    Optimized for minimal backtracks by employing Naked Singles, Hidden Singles,
    and MRV heuristic. Uses efficient candidate restoration on backtrack.
    """
    global BACKTRACKS
    BACKTRACKS = 0
    grid = [row[:] for row in grid]  # Create a copy

    # Candidate storage: dict of (row, col) -> set of possible values
    candidates = {}
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                candidates[(r, c)] = set(range(1, 10))

    def _get_peers(r, c):
        """Returns a set of peer coordinates for cell (r, c)."""
        peers = set()
        # Row peers
        for col in range(9):
            if col != c: peers.add((r, col))
        # Column peers
        for row in range(9):
            if row != r: peers.add((row, c))
        # Box peers
        box_r, box_c = (r // 3) * 3, (c // 3) * 3
        for i in range(box_r, box_r + 3):
            for j in range(box_c, box_c + 3):
                if (i, j) != (r, c): peers.add((i, j))
        return peers

    def _update_candidates_on_placement(r, c, num, current_candidates):
        """
        Removes 'num' from the candidate sets of peers of (r, c) in current_candidates.
        Returns True if successful, False if a contradiction is found.
        """
        if (r, c) in current_candidates:
            del current_candidates[(r, c)]

        for pr, pc in _get_peers(r, c):
            if (pr, pc) in current_candidates and num in current_candidates[(pr, pc)]:
                current_candidates[(pr, pc)].remove(num)
                if not current_candidates[(pr, pc)]:  # Contradiction
                    return False
        return True

    def _propagate_constraints(current_candidates):
        """
        Propagates Naked Singles and Hidden Singles until no more can be found.
        Modifies the grid in-place and updates current_candidates.
        Returns True if propagation is successful, False if a contradiction is found.
        """
        while True:
            changed = False
            # Naked Singles
            cells_to_remove = []
            for (r, c), possible_values in list(current_candidates.items()):
                if len(possible_values) == 1:
                    num = list(possible_values)[0]
                    grid[r][c] = num
                    if not _update_candidates_on_placement(r, c, num, current_candidates):
                        return False  # Contradiction
                    cells_to_remove.append((r, c))
                    changed = True
            
            for r, c in cells_to_remove:
                if (r, c) in current_candidates:
                    del current_candidates[(r, c)]

            if changed: continue

            # Hidden Singles
            for unit_type in range(3):  # 0: row, 1: col, 2: box
                for i in range(9):
                    num_positions = {num: [] for num in range(1, 10)}
                    unit_cells_coords = []

                    if unit_type == 0:  # Row
                        unit_cells_coords = [(i, c) for c in range(9)]
                    elif unit_type == 1:  # Column
                        unit_cells_coords = [(r, i) for r in range(9)]
                    else:  # Box
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
                                current_candidates[(r, c)] = {num}  # Convert to naked single
                                if not _update_candidates_on_placement(r, c, num, current_candidates):
                                    return False
                                changed = True
            if not changed:
                break
        return True

    def backtrack(current_candidates):
        """
        Recursive backtracking function.
        Selects a variable using MRV heuristic, tries values, and recurses.
        Restores state on backtrack efficiently.
        """
        global BACKTRACKS
        
        if not _propagate_constraints(current_candidates):
            return False

        if not current_candidates:  # All cells filled
            return True

        # Choose variable with Minimum Remaining Values (MRV)
        r, c = min(current_candidates, key=lambda k: len(current_candidates[k]))

        # Store current state of candidates for this cell for restoration
        original_cell_candidates = current_candidates[(r, c)].copy()

        # Try assigning values
        for num in sorted(list(original_cell_candidates)):
            grid[r][c] = num
            
            # Create a shallow copy of candidates for efficient rollback.
            # We only need to track changes made by _update_candidates_on_placement.
            temp_candidates_state = {k: v.copy() for k, v in current_candidates.items()}
            
            if _update_candidates_on_placement(r, c, num, current_candidates):
                if backtrack(current_candidates):
                    return True

            # Backtrack: Restore grid and candidates
            grid[r][c] = 0
            BACKTRACKS += 1
            current_candidates = temp_candidates_state # Restore candidates to state before assignment

        return False

    # Initial population of candidates and constraint propagation
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
                    return None # Initial grid is invalid

    if backtrack(initial_candidates):
        return grid
    return None