# Complete Development & Deployment System for Claude

**Goal**: Claude has full local development autonomy with one-command GPU execution on Colab.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Claude's Local Development Environment              │
│                   (This Environment)                         │
├─────────────────────────────────────────────────────────────┤
│ ✅ Edit code (Read/Write tools)                             │
│ ✅ Run tests (Bash commands)                                │
│ ✅ Git operations (Bash commands)                           │
│ ✅ Full project autonomy                                    │
└────────────────────┬──────────────────────────────────────┬─┘
                     │                                      │
        ┌────────────▼─────────────┐      ┌────────────────▼────┐
        │   GitHub Repository      │      │   Google Colab      │
        │  (Persistent Storage)    │      │   (GPU Execution)   │
        │                          │      │                     │
        │ - Auto-committed code    │      │ - Auto-clone latest │
        │ - All branches           │      │ - Install deps      │
        │ - Full history           │      │ - Run on GPU        │
        └────────────────────────┬─┘      │ - Save results      │
                                 │        └────────────┬────────┘
                                 │                     │
                          ┌──────▼─────────────────────▼──┐
                          │    Google Drive (Results)     │
                          │  /MyDrive/alz-gnn-results/    │
                          └──────────────────────────────┘
```

## Quick Start for Claude

### 1. Initial Setup (One Time)

```bash
# Inform user to:
python setup_colab.py  # They run this interactively once
# This configures GitHub remote automatically
```

### 2. Development Cycle

```
REPEAT:
  a) Edit code locally
  b) Test locally: pytest tests/test_baselines.py -v
  c) Deploy: python deploy_to_colab.py --task train
  d) Get Colab URL from output
  e) Share URL with user OR show results
```

### 3. After Each Deployment

The deployment script:
1. ✅ Commits pending changes to GitHub
2. ✅ Creates a Colab notebook
3. ✅ Outputs clickable Colab link
4. ✅ User clicks link → runs on GPU
5. ✅ Results auto-save to Google Drive

## Commands Claude Can Run

### Deploy to Colab (Main Command)

```bash
# Train models (most common)
python deploy_to_colab.py --task train

# With custom message
python deploy_to_colab.py --task train --message "Testing GAT improvements"

# Preprocess data
python deploy_to_colab.py --task preprocess

# Build graphs
python deploy_to_colab.py --task graph

# Download data
python deploy_to_colab.py --task download

# Run tests
python deploy_to_colab.py --task test

# Skip auto-commit if already done
python deploy_to_colab.py --task train --skip-git
```

### Local Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_baselines.py -v

# Run with coverage
pytest tests/ --cov=src

# Run specific test
pytest tests/test_baselines.py::TestBaselineModels::test_logistic_regression_training -v
```

### Code Changes

```bash
# Edit file locally
# Then check status
git status

# See what changed
git diff src/models/train.py

# Commit and push (deployment script does this)
git add .
git commit -m "Update training logic"
git push origin master
```

## Generated Colab Notebook Structure

When Claude runs `python deploy_to_colab.py`, it auto-generates a notebook with these cells:

```python
# Cell 1: GPU Check
!nvidia-smi

# Cell 2: Clone Latest Code
!git clone --branch master https://github.com/USERNAME/REPO.git /content/alz-gnn
%cd /content/alz-gnn

# Cell 3: Install Dependencies
!pip install -q torch torch-geometric anndata networkx scikit-learn optuna pyyaml

# Cell 4: Configure GPU
config['training']['device'] = 'cuda'

# Cell 5: Mount Google Drive
from google.colab import drive
drive.mount('/content/gdrive')

# Cell 6: Run Training
!python run.py train --mock

# Cell 7: Display Results
# Shows AUROC, accuracy, F1 scores

# Cell 8: Save to Drive
# Copies results to /gdrive/MyDrive/alz-gnn-results/
```

## File Reference

| File | Purpose | When to Use |
|------|---------|------------|
| `deploy_to_colab.py` | Main deployment script | `python deploy_to_colab.py --task train` |
| `setup_colab.py` | Initial GitHub setup | `python setup_colab.py` (user runs once) |
| `deploy.sh` | Quick bash wrapper | `./deploy.sh train` (Linux/Mac) |
| `COLAB_SETUP.md` | Complete guide | Reference for troubleshooting |
| `COLAB_QUICK_REF.md` | Quick commands | Look up commands quickly |
| `src/models/gnn_model.py` | GNN implementation | Edit to improve model |
| `src/models/baselines.py` | Baselines | Edit to improve baselines |
| `src/models/train.py` | Training orchestration | Edit to change training flow |
| `config.yaml` | Model configuration | Edit hyperparameters |

## Example Development Session

```bash
# 1. Claude edits gnn_model.py to improve attention mechanism
# (Using local Read/Write tools)

# 2. Claude tests improvements locally
pytest tests/test_gnn_model.py -v

# 3. Improvements look good, ready for GPU testing
python deploy_to_colab.py --task train --message "Improved attention weights calculation"

# 4. Script output:
#   "Deployement complete! Click here to run in Colab:"
#   "https://colab.research.google.com/github/USERNAME/REPO/blob/master/alz_gnn_colab_train.ipynb"

# 5. Share URL with user (or user clicks automatically)
# 6. Notebook runs on GPU, trains models
# 7. Results saved to Google Drive
# 8. User downloads or shares results

# 9. Claude reviews results and determines next improvements
# 10. Back to step 1
```

## Key Abilities Claude Now Has

| Capability | How | Status |
|------------|-----|--------|
| **Edit code locally** | Read/Write/Edit tools | ✅ Full control |
| **Test locally** | Bash commands (pytest) | ✅ Works locally |
| **Commit to GitHub** | Bash git commands | ✅ When deploying |
| **Deploy to Colab** | `python deploy_to_colab.py` | ✅ One command |
| **Monitor GPU training** | User clicks Colab link | ✅ Auto-generated notebook |
| **Access results** | Google Drive (auto-saved) | ✅ Results persist |
| **Full autonomy** | Complete local control + easy deployment | ✅ Combined system |

## Typical Iteration Pattern

```
Edit → Test → Deploy → GPU Train → Analyze → Improve → Repeat
```

From Claude's perspective:
```
1. (Local) cd c:/All-Code/Alzheimer-s_Research/alz-gnn-project
2. (Local) Edit src/models/gnn_model.py
3. (Local) Run: pytest tests/test_gnn_model.py -v
4. (Local) If tests pass: python deploy_to_colab.py --task train
5. (Colab) Notebook auto-runs on GPU (user clicks)
6. (Drive) Results saved automatically
7. (Local) Read results, analyze, plan improvements
8. Go to step 2
```

## Important Notes for Claude

### Before Deploying
- ✅ Always test locally with `pytest tests/` first
- ✅ Make sure code changes are working
- ✅ Check `git status` to see what will be committed
- ✅ Use clear commit messages (auto-provided in script)

### During Deployment
- ✅ The script automatically commits your changes
- ✅ Never manually push (deployment does it)
- ✅ Share the printed Colab URL with user
- ✅ Results are automatically saved

### After Training
- ✅ Results are in `/gdrive/MyDrive/alz-gnn-results/`
- ✅ Can access from any device
- ✅ Safe from Colab timeouts (Drive persists)
- ✅ User can download or share

## Autonomy Checklist

- [x] Read files locally (Alzheimer's-Research/alz-gnn-project)
- [x] Write/edit code locally
- [x] Commit to GitHub (deployment script)
- [x] Push to GitHub (deployment script)
- [x] Generate Colab notebooks (deployment script)
- [x] Get execution URLs (deployment script)
- [x] Run tests locally (pytest)
- [x] Access results (Google Drive)
- [x] Full development autonomy ✅

## Next Session Setup

When Claude returns in a new session:

1. Check if repo is initialized:
   ```bash
   git status  # Should show "On branch master"
   ```

2. If not, clone from GitHub:
   ```bash
   git clone https://github.com/USERNAME/REPO.git
   cd alz-gnn-project
   ```

3. Start development:
   ```bash
   python deploy_to_colab.py --task train
   ```

That's it! Full autonomy is set up and ready.

---

## Summary

Claude now has:
- **Complete local development autonomy** (edit, test, commit)
- **One-command GPU deployment** (deploy_to_colab.py)
- **Automatic result persistence** (Google Drive)
- **No manual Colab setup needed** (auto-generated notebooks)
- **Clear feedback loops** (results inform next iteration)

The system is designed for efficient iteration cycles where Claude can be completely autonomous in the development process while leveraging Colab's free GPU for training.
