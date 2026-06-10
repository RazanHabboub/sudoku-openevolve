def solve(grid, steps=None):
    if steps is None:
        steps = []
    grid = [row[:] for row in grid]
    backtracks = 0

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
        nonlocal backtracks
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
            backtracks += 1
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
                    return None, steps, backtracks

    result = grid if backtrack(initial_candidates) else None
    return result, steps, backtracks
