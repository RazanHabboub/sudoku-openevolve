# Sudoku OpenEvolve Project

## Team Members
- Razan Habboub
- Anna Li
- Isabel Delgado

## Project Overview

This project implements a mini OpenEvolve-style framework for evolving Sudoku-solving algorithms using LLM-guided code generation and automated evaluation.

The system starts with human-written baseline solvers and iteratively generates candidate solver implementations. Each candidate is evaluated for correctness and performance, and the best-performing variants are retained.

## Objectives

- Implement baseline Sudoku solvers
- Build an automated evaluation framework
- Generate solver variants using an LLM
- Compare evolved solvers against human-written baselines
- Analyze strengths and weaknesses of AI-driven algorithm optimization

## Repository Structure

```text
data/          Sudoku datasets
solvers/       Baseline and evolved solvers
candidates/    Generated solver variants
results/       Evaluation outputs and leaderboard
report/        Final report and presentation materials

evaluator.py   Candidate evaluation framework
evolve.py      Evolutionary search loop
prompts.py     LLM prompts
```

## Evaluation Metrics

- Solve rate
- Runtime
- Correctness
- Number of failed puzzles

## Baselines

1. Backtracking Solver
2. MRV (Minimum Remaining Values) Solver

## Expected Outcome

Determine whether an OpenEvolve-style search process can discover Sudoku-solving strategies that outperform baseline implementations while maintaining correctness.