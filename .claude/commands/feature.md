# Cross-Submodule Feature Workflow

Instructions for working on a feature that touches multiple submodules (backend, frontend, post_pipeline).

## Overview

When a feature requires changes across multiple repositories, you need to:
1. Create feature branches in each affected submodule
2. Work on each submodule independently

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


## Remember

The parent repository is your **integration branch**. It tracks which specific commits of each submodule are known to work together. Always keep it updated!
