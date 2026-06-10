#!/usr/bin/env python3
import argparse
import os
import sys
from math import ceil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from animation.solvers.backtracking_record import solve as bt_solve
from animation.solvers.mrv_record import solve as mrv_solve
from animation.solvers.naked_singles_record import solve as ns_solve
from animation.solvers.best_record import solve as best_solve
from animation.render import render_clip
from animation.compose import compose_4up, compose_2up

SOLVERS = [
    ('backtracking', bt_solve, 'Backtracking'),
    ('naked_singles', ns_solve, 'Naked Singles'),
    ('mrv', mrv_solve, 'MRV'),
    ('best', best_solve, 'Best Evolved'),
]

TARGET_SECONDS = {'easy': 6, 'hard': 10, 'expert': 10}
FPS = 30
OUTPUT_DIR = 'output'


def parse_puzzle(s):
    return [[int(s[r * 9 + c]) for c in range(9)] for r in range(9)]


def pick_puzzle(df, difficulty, override_idx=None):
    subset = df[df['difficulty'] == difficulty].reset_index(drop=True)
    if override_idx is not None:
        return parse_puzzle(subset.iloc[override_idx]['puzzle'])
    bt_counts = []
    for _, row in subset.iterrows():
        grid = parse_puzzle(row['puzzle'])
        _, _, bt = bt_solve(grid)
        bt_counts.append(bt)
    median_idx = sorted(range(len(bt_counts)), key=lambda i: bt_counts[i])[len(bt_counts) // 2]
    print(f"  [{difficulty}] selected puzzle index {median_idx} "
          f"(baseline bt={bt_counts[median_idx]})")
    return parse_puzzle(subset.iloc[median_idx]['puzzle'])


def main():
    parser = argparse.ArgumentParser(description='Generate Sudoku solver animation clips')
    parser.add_argument('--easy-idx', type=int, help='Puzzle index override for easy difficulty')
    parser.add_argument('--hard-idx', type=int, help='Puzzle index override for hard difficulty')
    parser.add_argument('--expert-idx', type=int, help='Puzzle index override for expert difficulty')
    parser.add_argument('--fps', type=int, default=FPS)
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.read_csv('data/eval_puzzles.csv')

    idx_overrides = {
        'easy': args.easy_idx,
        'hard': args.hard_idx,
        'expert': args.expert_idx,
    }

    composed_clips = {}

    for difficulty in ['easy', 'hard', 'expert']:
        print(f'\n=== {difficulty.upper()} ===')
        puzzle = pick_puzzle(df, difficulty, idx_overrides.get(difficulty))

        # Run all solvers and collect steps
        solver_results = {}
        for key, solve_fn, label in SOLVERS:
            _, steps, bt = solve_fn([row[:] for row in puzzle])
            solver_results[key] = (steps, bt, label)
            print(f'  {label}: {len(steps)} steps, {bt} backtracks')

        target_secs = TARGET_SECONDS[difficulty]
        total_frames = int(target_secs * args.fps)

        if difficulty == 'easy':
            # Shared speed: all solvers advance at the same rate.
            # Anchor to the slowest so no solver skips ahead.
            max_steps = max(len(v[0]) for v in solver_results.values()) or 1
            shared_spf = max(1, ceil(max_steps / total_frames))
            spf_map = {key: shared_spf for key, _, _ in SOLVERS}
            print(f'  [shared] steps_per_frame={shared_spf}, total_frames={total_frames}')
        else:
            # Per-solver speed for hard/expert: each solver fills the full duration
            # independently, so the best solver's moves are visible rather than
            # appearing instantaneous next to the high-backtrack solvers.
            spf_map = {key: max(1, ceil((len(solver_results[key][0]) or 1) / total_frames))
                       for key, _, _ in SOLVERS}
            print(f'  [per-solver] total_frames={total_frames}')
            for key, _, lbl in SOLVERS:
                print(f'    {lbl}: steps_per_frame={spf_map[key]}')

        clips = {}
        for key, solve_fn, label in SOLVERS:
            steps, bt, _ = solver_results[key]
            out = os.path.join(OUTPUT_DIR, f'{difficulty}_{key}.mp4')
            print(f'  Rendering {out} ...')
            render_clip(puzzle, steps, label, out, spf_map[key], total_frames, args.fps)
            clips[key] = out

        composed_clips[difficulty] = clips

    # Composed clips
    print('\n=== Composing ===')

    easy = composed_clips['easy']
    easy_4up = os.path.join(OUTPUT_DIR, 'easy_4up.mp4')
    compose_4up(
        [easy['backtracking'], easy['naked_singles'], easy['mrv'], easy['best']],
        easy_4up,
    )
    print(f'  {easy_4up}')

    for diff in ['hard', 'expert']:
        clips = composed_clips[diff]
        out = os.path.join(OUTPUT_DIR, f'{diff}_2up.mp4')
        compose_2up(clips['backtracking'], clips['best'], out)
        print(f'  {out}')

    print('\nDone! Output clips:')
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.mp4'):
            size_kb = os.path.getsize(os.path.join(OUTPUT_DIR, f)) // 1024
            print(f'  {f}  ({size_kb} KB)')


if __name__ == '__main__':
    main()
