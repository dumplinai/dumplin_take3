# Branch Status

Show current branches and available branches for the parent repo and all submodules.

## Instructions

Display the git branch information for:
1. The parent repository (`dumplin_take3`)
2. Each submodule (`backend`, `frontend`, `post_pipeline`)

For each repository, show:
- Current branch (highlighted)
- All available local branches
- Remote tracking information if applicable

## Output Format

```
=== Parent: dumplin_take3 ===
Current branch: <branch_name>
All branches:
  * <current_branch>
    <other_branch_1>
    <other_branch_2>

=== Submodule: backend ===
Current branch: <branch_name>
All branches:
  * <current_branch>
    <other_branch_1>

=== Submodule: frontend ===
Current branch: <branch_name>
All branches:
  * <current_branch>
    <other_branch_1>

=== Submodule: post_pipeline ===
Current branch: <branch_name>
All branches:
  * <current_branch>
    <other_branch_1>
```

## Commands to Run

Use these commands to gather the information:

```bash
# Parent repo
echo "=== Parent: dumplin_take3 ===" && \
git branch -vv && \
echo ""

# Backend submodule
echo "=== Submodule: backend ===" && \
cd backend && \
git branch -vv && \
cd .. && \
echo ""

# Frontend submodule
echo "=== Submodule: frontend ===" && \
cd frontend && \
git branch -vv && \
cd .. && \
echo ""

# Post Pipeline submodule
echo "=== Submodule: post_pipeline ===" && \
cd post_pipeline && \
git branch -vv && \
cd .. && \
echo ""
```

## Additional Context

Also show:
- Whether submodules are on detached HEAD state
- Remote tracking branch information
- Any uncommitted changes in each repository
