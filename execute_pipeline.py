#!/usr/bin/env python
"""
Execute the complete Alzheimer's biomarker discovery ML pipeline end-to-end.
This script runs all 8 stages of the pipeline and validates outputs.
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PipelineExecutor:
    """Execute the ML pipeline stages"""

    def __init__(self, project_root: str = None):
        """Initialize pipeline executor"""
        if project_root is None:
            project_root = str(Path(__file__).parent)

        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.results_dir = self.project_root / "results"
        self.data_dir = self.project_root / "data"

        # Create results directory if it doesn't exist
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Pipeline stages definition
        self.stages = [
            {
                "name": "Download datasets",
                "notebook": self.src_dir / "download" / "download_data.ipynb",
                "outputs": [self.data_dir / "raw"]
            },
            {
                "name": "Preprocess data",
                "notebook": self.src_dir / "preprocess" / "preprocess.ipynb",
                "outputs": [self.data_dir / "processed"]
            },
            {
                "name": "Construct graphs",
                "notebook": self.src_dir / "graphs" / "build_graphs.ipynb",
                "outputs": [self.data_dir / "processed" / "graphs"]
            },
            {
                "name": "Train baseline models",
                "notebook": self.src_dir / "models" / "baselines.ipynb",
                "outputs": [self.results_dir / "baseline_metrics.json"]
            },
            {
                "name": "Train GNN",
                "notebook": self.src_dir / "models" / "gnn_model.ipynb",
                "outputs": [self.results_dir / "models" / "model_checkpoint.pt"]
            },
            {
                "name": "Compute explanations",
                "notebook": self.src_dir / "explain" / "explain_model.ipynb",
                "outputs": [self.results_dir / "protein_attributions.csv"]
            },
            {
                "name": "Run stability analysis",
                "notebook": self.src_dir / "analysis" / "stability.ipynb",
                "outputs": [self.results_dir / "stability_report.md"]
            },
            {
                "name": "Generate final ranking",
                "notebook": self.src_dir / "analysis" / "final_ranking.ipynb",
                "outputs": [self.results_dir / "final_protein_targets.csv"]
            }
        ]

        self.execution_results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "summary": {
                "total_stages": len(self.stages),
                "completed": 0,
                "failed": 0,
                "errors": []
            }
        }

    def check_dependencies(self) -> bool:
        """Check if required packages are available"""
        logger.info("Checking dependencies...")
        required_packages = [
            "nbconvert",
            "jupyter",
            "torch",
            "pandas",
            "numpy"
        ]

        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)

        if missing:
            logger.error(f"Missing packages: {', '.join(missing)}")
            logger.info(f"Install with: pip install {' '.join(missing)}")
            return False

        logger.info("All dependencies available")
        return True

    def execute_notebook(self, notebook_path: Path, stage_name: str) -> Tuple[bool, str]:
        """Execute a Jupyter notebook"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Executing: {stage_name}")
        logger.info(f"Notebook: {notebook_path}")
        logger.info(f"{'='*70}")

        if not notebook_path.exists():
            error_msg = f"Notebook not found: {notebook_path}"
            logger.error(error_msg)
            return False, error_msg

        try:
            # Use nbconvert to execute the notebook
            output_notebook = self.results_dir / f"{notebook_path.stem}_executed.ipynb"

            cmd = [
                sys.executable,
                "-m",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--ExecutePreprocessor.timeout=3600",
                "--output",
                str(output_notebook),
                str(notebook_path)
            ]

            logger.info(f"Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=3600
            )

            # Log output
            if result.stdout:
                logger.info(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.info(f"STDERR:\n{result.stderr}")

            if result.returncode == 0:
                logger.info(f"Successfully executed: {stage_name}")
                return True, "Execution successful"
            else:
                error_msg = f"Execution failed with return code {result.returncode}"
                logger.error(error_msg)
                if result.stderr:
                    logger.error(f"Error details: {result.stderr}")
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "Execution timed out (3600 seconds)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error executing notebook: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return False, error_msg

    def validate_outputs(self, stage: Dict) -> bool:
        """Validate that expected outputs exist"""
        stage_name = stage["name"]
        outputs = stage["outputs"]

        logger.info(f"\nValidating outputs for: {stage_name}")
        all_exist = True

        for output_path in outputs:
            if isinstance(output_path, Path):
                exists = output_path.exists()
                logger.info(f"  {output_path.name}: {'✓' if exists else '✗'}")
                if not exists:
                    all_exist = False

        return all_exist

    def run_pipeline(self, use_mock: bool = True) -> Dict:
        """Run the complete pipeline"""
        logger.info("="*70)
        logger.info("ALZHEIMER'S BIOMARKER DISCOVERY ML PIPELINE")
        logger.info("="*70)
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Results directory: {self.results_dir}")
        logger.info(f"Mock data: {use_mock}")

        # Check dependencies
        if not self.check_dependencies():
            logger.error("Cannot proceed without dependencies")
            self.execution_results["summary"]["failed"] = 1
            return self.execution_results

        # Execute each stage
        for i, stage in enumerate(self.stages, 1):
            stage_name = stage["name"]
            notebook_path = stage["notebook"]

            logger.info(f"\n[{i}/{len(self.stages)}] {stage_name}")

            # Execute notebook
            success, message = self.execute_notebook(notebook_path, stage_name)

            # Record result
            self.execution_results["stages"][stage_name] = {
                "status": "completed" if success else "failed",
                "message": message,
                "notebook": str(notebook_path)
            }

            if success:
                self.execution_results["summary"]["completed"] += 1

                # Validate outputs
                outputs_valid = self.validate_outputs(stage)
                if not outputs_valid:
                    logger.warning(f"Some outputs missing for {stage_name}")
            else:
                self.execution_results["summary"]["failed"] += 1
                self.execution_results["summary"]["errors"].append({
                    "stage": stage_name,
                    "error": message
                })
                logger.error(f"Pipeline failed at stage: {stage_name}")
                # Continue to next stage for better diagnostics

        return self.execution_results

    def generate_report(self) -> str:
        """Generate final execution report"""
        report = []
        report.append("\n" + "="*70)
        report.append("PIPELINE EXECUTION REPORT")
        report.append("="*70)
        report.append(f"Timestamp: {self.execution_results['timestamp']}")
        report.append(f"\nSummary:")
        report.append(f"  Total stages: {self.execution_results['summary']['total_stages']}")
        report.append(f"  Completed: {self.execution_results['summary']['completed']}")
        report.append(f"  Failed: {self.execution_results['summary']['failed']}")

        report.append(f"\nStage Results:")
        for stage_name, result in self.execution_results["stages"].items():
            status = "✓" if result["status"] == "completed" else "✗"
            report.append(f"  {status} {stage_name}: {result['status']}")
            if result["message"]:
                report.append(f"      Message: {result['message']}")

        if self.execution_results["summary"]["errors"]:
            report.append(f"\nErrors:")
            for error in self.execution_results["summary"]["errors"]:
                report.append(f"  Stage: {error['stage']}")
                report.append(f"  Error: {error['error']}")

        # Check for output files
        report.append(f"\nOutput Files:")
        for stage in self.stages:
            outputs = stage["outputs"]
            for output_path in outputs:
                exists = "exists" if output_path.exists() else "missing"
                report.append(f"  [{exists}] {output_path}")

        report.append("\n" + "="*70)

        report_text = "\n".join(report)
        return report_text

    def save_results(self):
        """Save execution results to JSON"""
        results_file = self.results_dir / "pipeline_execution_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.execution_results, f, indent=2)
        logger.info(f"Results saved to: {results_file}")


def main():
    """Main execution function"""
    # Determine project root
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = str(Path(__file__).parent)

    # Create executor
    executor = PipelineExecutor(project_root)

    # Run pipeline (use mock data to avoid downloading large datasets)
    results = executor.run_pipeline(use_mock=True)

    # Generate and display report
    report = executor.generate_report()
    logger.info(report)

    # Save results
    executor.save_results()

    # Return exit code
    return 0 if results["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
