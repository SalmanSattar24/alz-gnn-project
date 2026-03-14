# Running on Google Colab - Complete Guide

This guide explains how to develop code locally in VS Code and execute it on Google Colab with full autonomy.

## Quick Start (TL;DR)

```bash
# 1. Edit code in VS Code (local)
# 2. Run deployment script
python deploy_to_colab.py --task train --message "Describe your changes"

# 3. Click the generated Colab URL
# 4. Run all cells (Ctrl+F9)
# 5. Results saved to Google Drive
```

---

## Full Workflow

### Prerequisites

1. **GitHub Repository** (public or private)
   ```bash
   # Create repo at https://github.com/USERNAME/Alzheimer-s-GNN
   # Clone locally if not already done
   cd ~/Projects/Alzheimer-s-GNN
   ```

2. **Google Account** with Colab access (free at colab.research.google.com)

3. **GitHub Token** (for private repos)
   - Go to https://github.com/settings/tokens
   - Create Personal Access Token with `repo` scope
   - Save token securely

### Local Development (VS Code)

```bash
# 1. Edit code in your editor
# 2. Test locally (if desired)
pytest tests/test_baselines.py -v

# 3. Commit all changes
git add .
git commit -m "Add feature X"
git push origin main

# OR use the deployment script (handles everything)
python deploy_to_colab.py --task train --message "Add feature X"
```

### Automatic Deployment to Colab

**Option A: Python Script (Recommended)**

```bash
# Deploy training to Colab
python deploy_to_colab.py --task train

# Deploy preprocessing to Colab
python deploy_to_colab.py --task preprocess

# Deploy with custom message
python deploy_to_colab.py --task train --message "Testing new GNN architecture"

# Skip git push (use if already committed)
python deploy_to_colab.py --task train --skip-git
```

**Option B: Shell Script**

```bash
# Make executable (Linux/Mac)
chmod +x deploy.sh

# Deploy
./deploy.sh train "Testing new feature"
./deploy.sh preprocess
./deploy.sh graph
```

### What deployment_to_colab.py does:

1. **Git Synchronization**
   - Commits all local changes
   - Pushes to GitHub
   - Captures repository URL, branch, commit hash

2. **Notebook Generation**
   - Creates a Jupyter notebook with pre-configured cells
   - Automatically clones latest code from GitHub
   - Sets up GPU environment
   - Installs dependencies
   - Runs your training/preprocessing task

3. **Provides Colab URLs**
   - Direct GitHub→Colab link (one-click execution)
   - Alternative upload options

### Execution in Colab

**Method 1: Direct GitHub URL (Simplest)**
```
1. Copy URL from deployment script output
2. Click link → Opens in Colab
3. Run all cells (Ctrl+F9) or one-by-one
4. Results saved to Google Drive
```

**Method 2: Upload Notebook**
```
1. Deployment script creates alz_gnn_colab_train.ipynb
2. Upload to Colab: https://colab.research.google.com/
3. Run cells
```

---

## Generated Colab Notebook Structure

The automatic notebook includes these cells:

```
Cell 1  : Environment info & GPU check
Cell 2  : Clone latest code from GitHub
Cell 3  : Install dependencies
Cell 4  : Configure for Colab GPU
Cell 5  : Mount Google Drive
Cell 6  : Run training/preprocessing
Cell 7  : Display results
Cell 8  : Save results to Google Drive
```

### Example Output

```
Epoch 000: Loss=0.7024, Val Loss=0.6925, Val AUROC=0.4950
Epoch 001: Loss=0.6812, Val Loss=0.6654, Val AUROC=0.5125
Epoch 002: Loss=0.6520, Val Loss=0.6389, Val AUROC=0.5456
...

Results files generated:
  - baseline_metrics.json (156 KB)
  - ROSMAP_gnn_training.json (89 KB)

Results saved to Google Drive: /gdrive/MyDrive/alz-gnn-results
```

---

## Workflow Examples

### Example 1: Quick Baseline Testing

```bash
# Local: Make improvements to baseline models
# Edit src/models/baselines.py

# Deploy to Colab for full training
python deploy_to_colab.py --task train --message "Improve baseline feature selection"

# Opens Colab automatically - click the link
# Runs on full GPU - takes ~5 minutes
# Results saved to Drive
```

### Example 2: GNN Training with Iterations

```bash
# Iteration 1: Initial GAT implementation
python deploy_to_colab.py --task train --message "GAT v1: Basic implementation"

# Colab results show AUROC=0.58, needs improvement

# Local: Adjust hyperparameters in config.yaml
# - Increase epochs to 200
# - Reduce learning rate to 0.0005

# Iteration 2: Deploy improved version
python deploy_to_colab.py --task train --message "GAT v2: Tuned hyperparameters"

# Colab runs v2 - AUROC improves to 0.72
```

### Example 3: Data Preprocessing Pipeline

```bash
# Add new data source
python deploy_to_colab.py --task download --message "Add GTEx tissue data"

# Preprocess new data
python deploy_to_colab.py --task preprocess --message "Normalize new tissues"

# Build graphs with updated data
python deploy_to_colab.py --task graph --message "Include tissue edges"

# Train on all datasets
python deploy_to_colab.py --task train --message "Train on all 3 cohorts + GTEx"
```

---

## Accessing Results

### Option 1: Download from Colab
Right-click on result files in Colab → Download

### Option 2: Google Drive (Recommended)
- Results auto-saved to `/gdrive/MyDrive/alz-gnn-results/`
- Access from any device
- Persistent storage even after Colab session ends
- Automatic backup

### Option 3: GitHub Actions
[For advanced users] Set up GitHub Actions to auto-commit results

```yaml
# .github/workflows/save_results.yml
name: Save Results
on: [push]
jobs:
  save:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: cp /path/to/results/* results/
      - run: git add results/ && git commit -m "Auto-save results"
```

---

## Troubleshooting

### Issue: "git not found" error
**Solution**: Install git on Windows from https://git-scm.com/

### Issue: "GitHub authentication failed"
**Solution**:
```bash
# For public repo: Should work automatically
# For private repo:
git config credential.helper store
git push  # Will prompt for token
```

### Issue: Colab session timeout (>12 hours)
**Solution**:
- Results are saved to Google Drive before issue occurs
- Re-run deployment script to resume training
- Colab keeps Drive files safe

### Issue: Out of memory in Colab
**Solution**: Reduce batch size in config.yaml
```yaml
training:
  batch_size: 16  # Reduce from 32
```

---

## Advanced: Custom Colab Commands

### Run specific cohort only

```bash
# Edit deploy_to_colab.py, modify notebook generation:
"!python run.py train --mock"  # Training only on ROSMAP
```

### Run tests in Colab

```python
python deploy_to_colab.py --task test
```

### Profile performance

```python
# Add to notebook:
!python -m cProfile -s cumtime run.py train --mock
```

---

## Summary Table

| Task | Local | Colab | Time |
|------|-------|-------|------|
| Edit code | VS Code | - | minutes |
| Deploy | `python deploy_to_colab.py` | Click URL | seconds |
| Train (mock) | `python run.py train --mock` | Auto (GPU) | 5-10 min |
| Full training | - | Auto (GPU) | 30-60 min |
| Results access | Local files | Google Drive | realtime |

---

## One-Command Alias (Optional)

Add to `.bashrc` or `.zshrc`:

```bash
alias colab='python deploy_to_colab.py'

# Usage:
colab --task train
colab --task test --message "Unit tests"
```

---

## Next Steps

1. **First deployment**:
   ```bash
   python deploy_to_colab.py --task train --message "First test run"
   ```

2. **Monitor in Colab**:
   - Watch GPU usage with `!nvidia-smi`
   - Check training progress in real-time

3. **Download results**:
   - From Google Drive or Colab directly
   - Analyze metrics locally

4. **Iterate**:
   - Make changes locally
   - Deploy again
   - Compare results

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    Your Local Machine                     │
│                        (VS Code)                          │
├──────────────────────────────────────────────────────────┤
│  ▪ Edit code (/src, /tests, config.yaml)                 │
│  ▪ Run: python deploy_to_colab.py                        │
│  ▪ Script commits to GitHub & generates notebook        │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │   GitHub Repo      │
        │  (Persistence)     │
        └────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Colab Notebook    │
        │  (Auto-Generated)  │
        │  ▪ Clones latest   │
        │  ▪ Installs deps   │
        │  ▪ Runs GPU train  │
        │  ▪ Saves to Drive  │
        └────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  Google Drive      │
        │  (Results Storage) │
        └────────────────────┘
```

---

## Support

For issues or questions:
1. Check logs in Colab cells
2. Verify `config.yaml` settings
3. Ensure GitHub repo is up-to-date: `git status`
4. Check internet connection (Colab requires it)
