"""
Pipeline automation script for Alzheimer's GNN project.

Provides CLI commands for running pipeline steps.
Usage: python run.py --help
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Define pipeline commands
COMMANDS = {
    "download": {
        "script": "src/download/download_data.py",
        "description": "Download data from Synapse",
    },
    "preprocess": {
        "script": "src/preprocess/preprocess.py",
        "description": "Preprocess and normalize data",
    },
    "graph": {
        "script": "src/graphs/build_graphs.py",
        "description": "Construct protein interaction graphs",
    },
    "train": {
        "script": "src/models/train.py",
        "description": "Train GNN models",
    },
    "explain": {
        "script": "src/explain/explain_model.py",
        "description": "Generate model explanations",
    },
    "stability": {
        "script": "src/analysis/stability_analysis.py",
        "description": "Run stability and robustness analysis",
    },
    "report": {
        "script": "src/analysis/generate_report.py",
        "description": "Generate comprehensive analysis report",
    },
}


def run_command(script: str, config: str = "config.yaml", use_mock: bool = False) -> int:
    """
    Run a pipeline script.

    Args:
        script: Path to script
        config: Config file path
        use_mock: Use mock data (for download command)

    Returns:
        Exit code
    """
    script_path = Path(script)
    if not script_path.exists():
        print(f"Error: Script not found: {script}")
        return 1

    try:
        # Convert to module path and run with -m flag for proper imports
        module_path = str(script_path.with_suffix("")).replace("\\", ".").replace("/", ".")
        cmd = [sys.executable, "-m", module_path, "--config", config]

        # Add --mock flag for download command
        if use_mock and "download" in script:
            cmd.append("--mock")

        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running {script}: {e}")
        return 1


def run_tests() -> int:
    """Run pytest suite."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-v"],
            check=False,
        )
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_lint() -> int:
    """Run linting checks."""
    print("Running flake8...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "src", "tests", "--max-line-length=100"],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode
    except Exception as e:
        print(f"Flake8 error: {e}")
        return 1

    print("\nRunning mypy...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "src", "--ignore-missing-imports"],
            check=False,
        )
        return result.returncode
    except Exception as e:
        print(f"Mypy error: {e}")
        return 1


def run_format() -> int:
    """Run code formatters."""
    print("Running black...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "src", "tests", "--line-length=100"],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode
    except Exception as e:
        print(f"Black error: {e}")
        return 1

    print("\nRunning isort...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "src", "tests", "--profile", "black"],
            check=False,
        )
        return result.returncode
    except Exception as e:
        print(f"Isort error: {e}")
        return 1


def clean() -> int:
    """Clean project artifacts."""
    import shutil
    import glob

    print("Cleaning project...")
    patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
        "*.egg-info",
    ]

    for pattern in patterns:
        for path in glob.glob(f"**/{pattern}", recursive=True):
            try:
                if Path(path).is_dir():
                    shutil.rmtree(path)
                else:
                    Path(path).unlink()
                print(f"  Removed: {path}")
            except Exception as e:
                print(f"  Error removing {path}: {e}")

    print("Cleanup complete")
    return 0


def run_all(config: str = "config.yaml", use_mock: bool = False) -> int:
    """Run complete pipeline."""
    steps = ["download", "preprocess", "graph", "train", "explain", "stability", "report"]
    print("Running complete pipeline...\n")

    for step in steps:
        print(f"\n{'='*60}")
        print(f"Step: {step.upper()}")
        print(f"{'='*60}")
        cmd_info = COMMANDS[step]
        result = run_command(cmd_info["script"], config, use_mock=use_mock)
        if result != 0:
            print(f"Pipeline failed at step: {step}")
            return result

    print(f"\n{'='*60}")
    print("Pipeline completed successfully!")
    print(f"{'='*60}")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Alzheimer's GNN Project - Pipeline Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py download              # Download data (real)
  python run.py download --mock       # Download data (mock)
  python run.py train --config config.yaml  # Train models
  python run.py all --mock            # Run complete pipeline with mock data
  python run.py test                  # Run tests
  python run.py lint                  # Run linting
  python run.py format                # Format code
  python run.py clean                 # Clean artifacts
        """,
    )

    parser.add_argument(
        "command",
        choices=list(COMMANDS.keys()) + ["test", "lint", "format", "clean", "all"],
        help="Command to run",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Configuration file path (default: config.yaml)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use synthetic mock data instead of downloading real datasets",
    )

    args = parser.parse_args()

    if args.command == "test":
        return run_tests()
    elif args.command == "lint":
        return run_lint()
    elif args.command == "format":
        return run_format()
    elif args.command == "clean":
        return clean()
    elif args.command == "all":
        return run_all(args.config, use_mock=args.mock)
    else:
        cmd_info = COMMANDS[args.command]
        print(f"{cmd_info['description']}...")
        return run_command(cmd_info["script"], args.config, use_mock=args.mock)


if __name__ == "__main__":
    sys.exit(main())
