# Cross-Submodule Feature Workflow

Instructions for working on a feature that touches multiple submodules (backend, frontend, post_pipeline).

## Overview

When a feature requires changes across multiple repositories, you need to:
1. Create feature branches in each affected submodule
2. Work on each submodule independently
3. Update parent repo to track compatible versions
4. Merge submodules first, then update parent

## Step 1: Setup Feature Branches

```bash
# In parent repo - create feature branch
git checkout -b feature/<feature-name>

# In backend submodule
cd backend/
git checkout main
git pull
git checkout -b feature/<feature-name>
cd ..

# In frontend submodule
cd frontend/
git checkout phase2  # or your main branch
git pull
git checkout -b feature/<feature-name>
cd ..

# In post_pipeline submodule (if needed)
cd post_pipeline/
git checkout main
git pull
git checkout -b feature/<feature-name>
cd ..
```

**Tip:** Use the same feature branch name across all repos for clarity.

## Step 2: Development Workflow

### Work on Backend
```bash
cd backend/
# Make your changes...
git add .
git commit -m "feat: description of backend changes"
git push -u origin feature/<feature-name>
cd ..

# Update parent to track backend changes
git add backend
git commit -m "Update backend submodule: <description>"
git push
```

### Work on Frontend
```bash
cd frontend/
# Make your changes...
git add .
git commit -m "feat: description of frontend changes"
git push -u origin feature/<feature-name>
cd ..

# Update parent to track frontend changes
git add frontend
git commit -m "Update frontend submodule: <description>"
git push
```

### Work on Post Pipeline (if needed)
```bash
cd post_pipeline/
# Make your changes...
git add .
git commit -m "feat: description of pipeline changes"
git push -u origin feature/<feature-name>
cd ..

# Update parent to track pipeline changes
git add post_pipeline
git commit -m "Update post_pipeline submodule: <description>"
git push
```

## Step 3: Check Status Across All Repos

```bash
# Use /branch command to see all branches
/branch

# Or check manually
git status
echo "---"
cd backend && git status && cd ..
echo "---"
cd frontend && git status && cd ..
echo "---"
cd post_pipeline && git status && cd ..
```

## Step 4: Testing Integration

While on the feature branch in the parent repo, all submodules are on their feature branches. Test that everything works together before merging.

```bash
# Parent repo shows which commits of each submodule are tested together
git submodule status
```

## Step 5: Merging (When Feature is Complete)

**IMPORTANT:** Always merge submodules BEFORE updating parent to main.

### Merge Backend
```bash
cd backend/
git checkout main
git pull
git merge feature/<feature-name>
git push
cd ..
```

### Merge Frontend
```bash
cd frontend/
git checkout phase2  # or your main branch
git pull
git merge feature/<feature-name>
git push
cd ..
```

### Merge Post Pipeline (if changed)
```bash
cd post_pipeline/
git checkout main
git pull
git merge feature/<feature-name>
git push
cd ..
```

### Update Parent to Track Merged Commits
```bash
# Update submodules to point to the newly merged commits
git submodule update --remote backend frontend post_pipeline

# Add the submodule updates
git add backend frontend post_pipeline
git commit -m "Update submodules to merged feature/<feature-name>"

# Merge parent feature branch to main
git checkout <main-branch>
git pull
git merge feature/<feature-name>
git push
```

## Quick Reference Commands

### Start New Feature
```bash
# One-liner to create feature branches everywhere
git checkout -b feature/<name> && \
cd backend && git checkout -b feature/<name> && cd .. && \
cd frontend && git checkout -b feature/<name> && cd ..
```

### Commit to Submodule + Update Parent
```bash
# Example for backend
cd backend && git add . && git commit -m "msg" && git push && cd .. && \
git add backend && git commit -m "Update backend: msg" && git push
```

### Check All Statuses
```bash
echo "PARENT:" && git status && \
echo -e "\nBACKEND:" && cd backend && git status && cd .. && \
echo -e "\nFRONTEND:" && cd frontend && git status && cd .. && \
echo -e "\nPIPELINE:" && cd post_pipeline && git status && cd ..
```

## Best Practices

1. **Same Branch Names:** Use identical feature branch names across submodules for clarity
2. **Update Parent Frequently:** Every submodule commit should update the parent
3. **Test Integration:** The parent feature branch lets you test that all components work together
4. **Merge Order:** Always merge submodules to their main branches FIRST, then update parent
5. **Atomic Compatibility:** Parent repo ensures you always have a set of compatible submodule versions

## Example Feature Flow

```
Day 1:
- Create feature/user-auth in backend, frontend, parent
- Add auth endpoint in backend → commit → push → update parent
- Test endpoint works

Day 2:
- Add login UI in frontend → commit → push → update parent
- Test full login flow works (integration test)

Day 3:
- Merge backend/feature/user-auth to backend/main
- Merge frontend/feature/user-auth to frontend/phase2
- Update parent submodules to merged commits
- Merge parent/feature/user-auth to parent/main
```

## Common Issues

**Detached HEAD in Submodule:**
```bash
cd backend/
git checkout feature/<feature-name>
cd ..
```

**Submodule on Wrong Commit:**
```bash
cd backend/
git checkout <correct-branch>
git pull
cd ..
git add backend
git commit -m "Update backend to correct branch"
```

**Forgot to Update Parent:**
```bash
# After committing to submodule
git add backend  # or frontend, post_pipeline
git commit -m "Update submodule to latest"
git push
```

## Remember

The parent repository is your **integration branch**. It tracks which specific commits of each submodule are known to work together. Always keep it updated!
