#!/bin/bash
# Quick deployment script for Colab
# Usage: ./deploy.sh [task] [message]

TASK="${1:-train}"
MESSAGE="${2:-Auto-deploy: $TASK}"

echo "=========================================="
echo "Deploying to Colab: $TASK"
echo "=========================================="

python deploy_to_colab.py --task "$TASK" --message "$MESSAGE"
