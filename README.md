# Sudoku OpenEvolve Project

## Team Members
- Razan Habboub
- Anna Li
- Isabel Delgado

## Project Overview

This project implements an OpenEvolve-style evolutionary framework for improving Sudoku-solving algorithms using LLM-guided code generation and automated evaluation.

The system seeds an evolutionary loop with a human-written baseline solver. Each iteration, an LLM receives the current best program as context and proposes a modified variant. Candidates are evaluated against 150 puzzles under a per-puzzle timeout; the best-scoring program becomes the parent for the next generation. Evolution uses MAP-Elites with island-based population management (3 islands, periodic migration) to maintain diversity. The LLM backend is Gemini 2.5 Flash Lite.

## Objectives

- Implement baseline Sudoku solvers
- Build an automated evaluation framework
- Generate solver variants using an LLM
- Compare evolved solvers against human-written baselines
- Analyze strengths and weaknesses of AI-driven algorithm optimization

## Repository Structure

```text
data/                   Sudoku datasets (Kaggle easy, tdoku forum-hardest hard/expert)
solvers/                Human-written baseline solvers
results/                Checkpoints, best program, and run logs
results/best/           Best evolved program
results/checkpoints/    Periodic snapshots of the population
results/logs/           Full OpenEvolve run logs
animation/              Solver step-recording infrastructure (in progress)
prompts/                LLM system prompt

config.yaml             OpenEvolve configuration
evaluator.py            Standalone baseline benchmarking script
openevolve_evaluate.py  OpenEvolve evaluation bridge (called each iteration)
evolve.py               Evolutionary search entry point
```

## Evaluation Metrics

Fitness is **backtrack efficiency** over 150 puzzles (100 easy / 25 hard / 25 expert) with a 1.5-second per-puzzle timeout:

- Each solved puzzle contributes its actual backtrack count
- Each unsolved or timed-out puzzle contributes a penalty of 1,500,000
- `avg_bt = sum(puzzle_bt) / 150`
- `combined_score = 1 / (1 + avg_bt / 303708)` — maximized by the search

A score of 0.50 corresponds to the seed baseline (~303K avg backtracks). A score of 1.00 would mean zero backtracks.

## Baselines

All three baselines solve 100% of puzzles given unlimited time. Under the 1.5s timeout they differ substantially on hard and expert puzzles.

1. **Backtracking** — picks the first empty cell, tries values 1–9 in order, recurses, undoes on failure
2. **MRV** — same as backtracking but always branches on the cell with fewest remaining candidates (Minimum Remaining Values)
3. **Naked Singles** — propagates cells with exactly one candidate to a fixpoint before handing off to MRV backtracking

The backtracking solver was used as the seed for OpenEvolve.

## Results

After 90+ iterations the best evolved program achieves:

| Metric | Baseline (backtracking) | Best Evolved |
|---|---|---|
| Combined score | 0.5004 | 0.9997 |
| Avg backtracks | 303,279 | 91 |
| Overall solve rate | 80% | 100% |
| Easy solve rate | 100% | 100% |
| Hard solve rate | 12% | 100% |
| Expert solve rate | 68% | 100% |

The best program was discovered at **iteration 15** and never surpassed. It independently rediscovered constraint propagation techniques — naked singles, hidden singles, forward checking, and MRV-guided branching — achieving a ~3,300x reduction in average backtracks.
