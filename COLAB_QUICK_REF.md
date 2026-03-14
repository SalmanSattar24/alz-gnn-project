# Colab Deployment Quick Reference

## One-Line Commands

```bash
# Training
python deploy_to_colab.py --task train --message "Your description"

# Preprocessing
python deploy_to_colab.py --task preprocess

# Graph building
python deploy_to_colab.py --task graph

# Testing
python deploy_to_colab.py --task test

# Full pipeline
python deploy_to_colab.py --task download && \
python deploy_to_colab.py --task preprocess && \
python deploy_to_colab.py --task graph && \
python deploy_to_colab.py --task train
```

## What Happens Automatically

1. ✅ Commits pending code changes to GitHub
2. ✅ Generates a Colab notebook
3. ✅ Prints clickable Colab link
4. ✅ Notebook auto-clones latest code
5. ✅ Runs on Colab GPU
6. ✅ Saves results to Google Drive

## Typical Workflow (per iteration)

```bash
# 1. Edit code locally in VS Code
# 2. When ready to test on GPU:
python deploy_to_colab.py --task train

# 3. Click printed URL (opens Colab)
# 4. Press Ctrl+F9 to run all cells
# 5. Check results on Google Drive
# 6. Download or iterate again
```

## Common Scenarios

| Task | Command |
|------|---------|
| Quick test run | `python deploy_to_colab.py --task train` |
| Full training | `python deploy_to_colab.py --task train --message "Full training run"` |
| Baseline models only | Edit config.yaml `training.epochs: 50`, then deploy |
| GNN only | Edit config.yaml, then `python deploy_to_colab.py --task train` |
| Skip git push | `python deploy_to_colab.py --task train --skip-git` |

## Generated Notebook Name

File: `alz_gnn_colab_TASK.ipynb` (e.g., `alz_gnn_colab_train.ipynb`)

## Colab Performance

- **GPU Type**: NVIDIA T4 or P100 (free tier lucky draw)
- **Memory**: 12.7 GB GPU + 27 GB RAM
- **Training Speed**: ~10x faster than CPU
- **Timeout**: 12 hours per session
- **Cost**: Free

## Results Storage

Auto-saves to: `/content/gdrive/MyDrive/alz-gnn-results/`

Download via:
- Google Drive web interface
- Colab Files panel (left sidebar)
- Direct download from Colab cells

## Tips

1. **Save time**: Use `--skip-git` if already committed
2. **Check status**: `!git log --oneline -1` in Colab first cell
3. **Reduce training**: Modify `config.yaml` epochs before deploy
4. **Use mock data**: Scripts default to `--mock` flag for faster testing
5. **Monitor GPU**: Colab shows GPU usage in UI (free tier varies)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Import errors | Check `requirements.txt` in deploy script |
| Out of GPU memory | Reduce batch_size in config.yaml |
| Colab session timeout | Results saved to Drive; re-deploy to continue |
| GitHub auth error | Check git config: `git config --list` |
