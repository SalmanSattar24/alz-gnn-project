"""
Deploy code to GitHub and generate Colab notebook.

This script handles the entire deployment workflow:
1. Commits all changes to GitHub
2. Pushes to remote
3. Generates a runnable Colab notebook
4. Prints the Colab execution URL
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
import argparse

def run_command(cmd: str, check=True) -> str:
    """Run a shell command and return output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout + result.stderr

def git_sync(message: str = None):
    """Commit and push all changes to GitHub."""
    print("\n" + "="*60)
    print("STEP 1: Git Synchronization")
    print("="*60)

    if message is None:
        message = input("Commit message (default: 'Update code'): ").strip()
        if not message:
            message = "Update code"

    # Check git status
    status = run_command("git status --porcelain")

    if not status.strip():
        print("No changes to commit. Skipping git push.")
        return True

    # Stage all changes
    print("\nStaging changes...")
    run_command("git add -A")

    # Commit
    print(f"\nCommitting with message: {message}")
    run_command(f'git commit -m "{message}"')

    # Push
    print("\nPushing to GitHub...")
    run_command("git push origin HEAD")

    print("Git sync complete!")
    return True

def get_git_info() -> dict:
    """Get current git repository information."""
    try:
        repo_url = run_command("git config --get remote.origin.url", check=False).strip()
        if not repo_url:
            print("\nERROR: No GitHub remote configured!")
            print("To set up, run:")
            print("  git remote add origin https://github.com/USERNAME/REPO.git")
            print("Then:")
            print("  git push -u origin master")
            exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure you're in a git repository and have set up the remote.")
        exit(1)

    branch = run_command("git rev-parse --abbrev-ref HEAD", check=False).strip()
    commit = run_command("git rev-parse --short HEAD", check=False).strip()

    # Clean up git URL variations
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    if "git@github" in repo_url:
        repo_url = repo_url.replace("git@github.com:", "https://github.com/")
        repo_url = repo_url.replace(":", "/")

    return {
        "url": repo_url,
        "branch": branch,
        "commit": commit,
    }

def create_colab_notebook(git_info: dict, task: str = "train") -> str:
    """Generate a Colab notebook for execution."""
    print("\n" + "="*60)
    print("STEP 2: Creating Colab Notebook")
    print("="*60)

    repo_url = git_info["url"]
    branch = git_info["branch"]
    commit = git_info["commit"]

    # Colab notebook cells
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Alzheimer's GNN - Colab Execution\n",
                f"**Repository**: [{repo_url.split('/')[-1]}]({repo_url})\n",
                f"**Branch**: {branch}\n",
                f"**Commit**: {commit}\n",
                f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                "\n",
                "This notebook automatically clones the latest code and runs training on GPU."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Check GPU availability\n",
                "!nvidia-smi"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Clone repository\n",
                "!rm -rf /content/alz-gnn 2>/dev/null\n",
                f"!git clone --branch {branch} {repo_url}.git /content/alz-gnn\n",
                "%cd /content/alz-gnn\n",
                "\n",
                "# Show current commit\n",
                "!git log --oneline -1"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Install dependencies\n",
                "print('Installing dependencies...')\n",
                "!pip install -q torch torch-geometric anndata networkx scikit-learn optuna pyyaml pandas numpy"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Configure for Colab GPU\n",
                "import yaml\n",
                "\n",
                "with open('config.yaml', 'r') as f:\n",
                "    config = yaml.safe_load(f)\n",
                "\n",
                "# Use Colab GPU\n",
                "config['training']['device'] = 'cuda'\n",
                "config['training']['num_workers'] = 4\n",
                "\n",
                "with open('config.yaml', 'w') as f:\n",
                "    yaml.dump(config, f)\n",
                "\n",
                "print('✓ Configured for Colab GPU')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Mount Google Drive (optional, for saving results)\n",
                "from google.colab import drive\n",
                "drive.mount('/content/gdrive', force_remount=True)\n",
                "print('✓ Google Drive mounted at /content/gdrive')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Run training\n",
                f"!python run.py {task} --mock"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Display results\n",
                "import json\n",
                "from pathlib import Path\n",
                "\n",
                "results_dir = Path('results/models')\n",
                "json_files = list(results_dir.glob('*_metrics.json')) + list(results_dir.glob('*_training.json'))\n",
                "\n",
                "if json_files:\n",
                "    print('Results files generated:')\n",
                "    for f in sorted(json_files):\n",
                "        print(f'  - {f.name} ({f.stat().st_size / 1024:.1f} KB)')\n",
                "        \n",
                "    # Show baseline metrics if available\n",
                "    baseline_file = results_dir / 'baseline_metrics.json'\n",
                "    if baseline_file.exists():\n",
                "        print(f'\\n=== Baseline Metrics (ROSMAP) ===')\n",
                "        with open(baseline_file) as f:\n",
                "            data = json.load(f)\n",
                "            if 'ROSMAP' in data:\n",
                "                for model, results in data['ROSMAP'].items():\n",
                "                    if 'test_metrics' in results:\n",
                "                        print(f'\\n{model.upper()}:')\n",
                "                        for metric, val in results['test_metrics'].items():\n",
                "                            print(f'  {metric}: {val:.4f}')\n",
                "else:\n",
                "    print('No results files found. Check training output above.')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Save results to Google Drive\n",
                "import shutil\n",
                "from pathlib import Path\n",
                "\n",
                "results_src = Path('results')\n",
                "results_dst = Path('/content/gdrive/MyDrive/alz-gnn-results')\n",
                "results_dst.mkdir(parents=True, exist_ok=True)\n",
                "\n",
                "if results_src.exists():\n",
                "    # Copy results directory\n",
                "    for item in results_src.rglob('*'):\n",
                "        if item.is_file():\n",
                "            rel_path = item.relative_to(results_src)\n",
                "            dest = results_dst / rel_path\n",
                "            dest.parent.mkdir(parents=True, exist_ok=True)\n",
                "            shutil.copy2(item, dest)\n",
                "    \n",
                "    print(f'✓ Results saved to Google Drive: {results_dst}')\n",
                "else:\n",
                "    print('No results to save')"
            ]
        }
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "colab": {
                "name": f"Alzheimer-GNN-{task}-{datetime.now().strftime('%Y%m%d')}",
                "provenance": [],
                "toc_visible": True,
                "backends": ["colab"],
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.12"
            },
            "accelerator": "GPU"
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    # Save notebook
    notebook_path = Path(f"alz_gnn_colab_{task}.ipynb")
    with open(notebook_path, 'w') as f:
        json.dump(notebook, f, indent=2)

    print(f"✓ Notebook created: {notebook_path}")
    return str(notebook_path)

def generate_colab_urls(notebook_path: str) -> dict:
    """Generate Colab URLs for the notebook."""
    notebook_path = Path(notebook_path)
    git_info = get_git_info()

    # GitHub raw URL
    repo_parts = git_info["url"].split("/")
    owner = repo_parts[-2]
    repo = repo_parts[-1]

    # Direct GitHub upload URL
    github_upload_url = f"https://colab.research.google.com/github/{owner}/{repo}/blob/{git_info['branch']}/{notebook_path}"

    # Local upload (user needs to upload first)
    local_upload_url = "https://colab.research.google.com/notebook"

    return {
        "github": github_upload_url,
        "github_from_repo": f"https://github.com/{owner}/{repo}/blob/{git_info['branch']}/{notebook_path}",
    }

def main():
    parser = argparse.ArgumentParser(description="Deploy to Colab")
    parser.add_argument("--task", default="train", choices=["train", "test", "preprocess", "graph", "download"],
                       help="Task to run in Colab")
    parser.add_argument("--message", default=None, help="Git commit message")
    parser.add_argument("--skip-git", action="store_true", help="Skip git push")
    parser.add_argument("--skip-notebook", action="store_true", help="Skip notebook generation")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("COLAB DEPLOYMENT SCRIPT")
    print("="*60)

    # Step 1: Git sync
    if not args.skip_git:
        if not git_sync(args.message):
            print("Git sync failed!")
            return False

    # Get git info
    git_info = get_git_info()
    print(f"\nRepository: {git_info['url']}")
    print(f"Branch: {git_info['branch']}")
    print(f"Commit: {git_info['commit']}")

    # Step 2: Create notebook
    notebook_path = None
    if not args.skip_notebook:
        notebook_path = create_colab_notebook(git_info, args.task)

    # Step 3: Print Colab URLs
    print("\n" + "="*60)
    print("STEP 3: Colab Execution URLs")
    print("="*60)

    if notebook_path:
        urls = generate_colab_urls(notebook_path)

        print("\nOption 1: Run directly from GitHub")
        print(f"  {urls['github']}")

        print("\nOption 2: View notebook on GitHub")
        print(f"  {urls['github_from_repo']}")

        print("\nOption 3: Upload local notebook to Colab")
        print(f"  1. Upload {notebook_path} to Colab")
        print(f"  2. Open in Colab: {urls['github']}")

    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Click the URL above to open in Colab")
    print("2. Run all cells (Ctrl+F9) or run them individually")
    print("3. Results will be saved to Google Drive (if mounted)")

    return True

if __name__ == "__main__":
    main()
