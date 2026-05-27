# Skill: Worktree Helper

## Purpose

Use Git worktrees to work on multiple features simultaneously without stashing or switching branches. Especially useful when implementing backend and frontend in parallel.

## Setup

```bash
# From repo root — create a worktree for frontend work
git worktree add ../fleet-frontend feat/frontend-dashboard

# Work in the worktree
cd ../fleet-frontend
# ... make changes, commit ...

# List worktrees
git worktree list

# Remove when done (after merging)
git worktree remove ../fleet-frontend
```

## When to Use in This Challenge

| Scenario | Worktree? |
|----------|-----------|
| Backend and frontend in parallel | Yes — keeps branch histories separate |
| Two backend features simultaneously | Yes — no stash needed |
| Quick fix on a different branch | Sometimes — depends on size |
| Single focused feature | No — regular branch is fine |

## Common Commands

```bash
# Add a worktree for a new feature branch
git worktree add <path> -b <new-branch>

# Add a worktree for an existing branch
git worktree add <path> <existing-branch>

# Prune stale worktree metadata
git worktree prune

# Show all worktrees with their branches
git worktree list --porcelain
```

## Gotchas

- Same branch cannot be checked out in two worktrees simultaneously.
- `git stash` is shared across worktrees — be careful with stash pop in the wrong worktree.
- Each worktree has its own working tree but shares the same `.git` object store.
- IDE indexing may get confused by multiple worktrees — open each in its own IDE window.
