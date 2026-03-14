#!/usr/bin/env python3
"""
Setup script for Colab deployment.

This configures GitHub remote and validates the environment.
Run this once at the beginning.
"""

import subprocess
import sys
from pathlib import Path

# Use simple ASCII characters for Windows compatibility
OK = "[OK]"
FAIL = "[X]"
WARN = "[!]"

def run_cmd(cmd: str, check=True) -> tuple:
    """Run command and return (success, output)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return True, result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def validate_git_repo():
    """Check if we're in a git repository."""
    success, _ = run_cmd("git status")
    if not success:
        print("ERROR: Not a git repository!")
        print("Run: cd to your project directory")
        return False
    return True

def has_git_remote():
    """Check if origin remote is configured."""
    success, output = run_cmd("git config --get remote.origin.url", check=False)
    return success and output.strip()

def setup_github_remote():
    """Interactive setup for GitHub remote."""
    print("\n" + "="*60)
    print("GitHub Remote Configuration")
    print("="*60)

    print("\nYou need to provide your GitHub repository URL.")
    print("Example: https://github.com/USERNAME/Alzheimer-s-GNN")
    print("Or: git@github.com:USERNAME/Alzheimer-s-GNN.git")

    while True:
        repo_url = input("\nEnter your GitHub repo URL: ").strip()

        if not repo_url:
            print("URL cannot be empty!")
            continue

        if "github" not in repo_url:
            print("URL must be a GitHub repository!")
            continue

        # Add remote
        success, output = run_cmd(f"git remote add origin {repo_url}", check=False)

        if "already exists" in output:
            print("Remote 'origin' already configured!")
            confirm = input("Update it? (y/n): ").lower()
            if confirm == "y":
                run_cmd(f"git remote set-url origin {repo_url}")
                print("Remote updated!")
            break
        elif success:
            print(f"Remote configured!")
            break
        else:
            print(f"Error: {output}")
            continue

    return True

def validate_requirements():
    """Check if main requirements are installed."""
    print("\n" + "="*60)
    print("Checking Dependencies")
    print("="*60)

    required = {
        "git": "Git",
        "python": "Python",
        "python -m pip": "pip",
    }

    all_ok = True
    for cmd, name in required.items():
        success, output = run_cmd(f"{cmd} --version", check=False)
        if success:
            version = output.strip().split('\n')[0]
            print(f"{OK} {name:15} {version}")
        else:
            print(f"{FAIL} {name:15} NOT FOUND")
            all_ok = False

    return all_ok

def main():
    print("\n" + "="*60)
    print("COLAB DEPLOYMENT SETUP")
    print("="*60)

    # 1. Check git repo
    print("\n[1/4] Checking git repository...")
    if not validate_git_repo():
        print("Please initialize git repo: git init")
        return False
    print(f"{OK} Git repository found")

    # 2. Check remote
    print("\n[2/4] Checking GitHub remote...")
    if not has_git_remote():
        print(f"{WARN} GitHub remote not configured")
        if not setup_github_remote():
            return False
    else:
        success, url = run_cmd("git config --get remote.origin.url", check=False)
        if success:
            print(f"{OK} Remote configured: {url.strip()}")

    # 3. Check dependencies
    print("\n[3/4] Checking dependencies...")
    if not validate_requirements():
        print("\nSome dependencies are missing. Install them:")
        print("  Windows: https://git-scm.com/download/win")
        print("  macOS: brew install git")
        print("  Linux: apt-get install git")
        # Don't fail here, user can continue

    # 4. Test deployment script
    print("\n[4/4] Testing deployment script...")
    deploy_script = Path("deploy_to_colab.py")
    if deploy_script.exists():
        success, _ = run_cmd("python deploy_to_colab.py --help", check=False)
        if success:
            print(f"{OK} Deployment script ready")
        else:
            print(f"{FAIL} Deployment script error")
            return False
    else:
        print(f"{FAIL} deploy_to_colab.py not found!")
        return False

    # Success!
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)

    print("\nYou're ready to deploy to Colab!")
    print("\nNext steps:")
    print("  1. Edit your code in VS Code")
    print("  2. Run: python deploy_to_colab.py --task train")
    print("  3. Click the Colab URL")
    print("  4. Run cells on GPU!")

    print("\nQuick start commands:")
    print("  python deploy_to_colab.py --task train --message 'Initial run'")
    print("  python deploy_to_colab.py --task preprocess")
    print("  python deploy_to_colab.py --task graph")

    print("\nFor more info, see COLAB_SETUP.md")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
