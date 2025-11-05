# GitHub Repository Schema

Explain the Dumplin project's GitHub repository structure and submodule architecture.

## Repository Structure

### Parent Repository
- **Repo:** `dumplinai/dumplin_take3`
- **Purpose:** Container repository that orchestrates all components via git submodules
- **Contains:**
  - `.gitmodules` - Submodule configuration
  - `specs/` - Shared specifications and documentation
  - `.claude/` - Shared Claude Code configurations
  - References to backend, frontend, and post_pipeline submodules

### Component Repositories (Submodules)

#### Backend
- **Repo:** `dumplinai/backend`
- **Branch:** main
- **Tech:** FastAPI Python application
- **Purpose:** API server and business logic

#### Frontend
- **Repo:** `dumplinai/frontend`
- **Branch:** phase2
- **Tech:** Flutter mobile application
- **Purpose:** Mobile user interface

#### Post Pipeline
- **Repo:** `dumplinai/post_pipeline`
- **Branch:** main
- **Tech:** Python data pipeline
- **Purpose:** Data ingestion and processing

## How It Works

### Storage
- Each component repo stores its own code independently on GitHub
- The parent repo (`dumplin_take3`) ONLY stores:
  - Commit hash references to specific versions of each submodule
  - Shared files (specs, .claude configs, etc.)
  - `.gitmodules` file with submodule URLs

### No Duplication
- Code is NOT duplicated across repositories
- Submodule folders in parent repo are just pointers to commits in component repos
- Total parent repo size: ~50 KB (just references and shared files)

## Common Workflows

### For Full Stack Development
```bash
# Clone with all submodules
git clone --recurse-submodules https://github.com/dumplinai/dumplin_take3.git

# Update parent and sync to tracked commits
git pull && git submodule update --init --recursive

# Update all submodules to latest
git pull && git submodule update --remote --recursive
```

### For Single Component Development
```bash
# Clone only the component you need
git clone https://github.com/dumplinai/backend.git
# or
git clone https://github.com/dumplinai/frontend.git
# or
git clone https://github.com/dumplinai/post_pipeline.git
```

### Updating a Submodule
```bash
# 1. Work in the submodule
cd backend/
git checkout main
git pull
# Make changes...
git add . && git commit -m "Update feature"
git push

# 2. Update parent to track new commit
cd ..
git add backend
git commit -m "Update backend submodule to latest"
git push
```

### Developer Access Control
- **Frontend only dev:** Clone `dumplinai/frontend` directly (won't see backend code)
- **Backend only dev:** Clone `dumplinai/backend` directly (won't see frontend code)
- **Full team lead:** Clone `dumplinai/dumplin_take3` with submodules

## Quick Reference

```bash
# View submodule status
git submodule status

# Initialize specific submodule only
git submodule update --init frontend

# Update to commits specified by parent
git submodule update --init --recursive

# Update to latest commits on remote
git submodule update --remote --recursive

# See what commit each submodule is on
git submodule foreach 'git log -1 --oneline'
```

## Key Principles
1. **Single Source of Truth:** Each component repo is the source of truth for that component
2. **Version Coordination:** Parent repo tracks which versions work together
3. **Independent Development:** Teams can work on components independently
4. **Atomic Deployments:** Parent repo ensures compatible versions are deployed together
