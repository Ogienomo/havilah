#!/bin/bash
# Havilah OS — Push to GitHub
# Run this script after providing your GitHub credentials
#
# Option 1: Set GITHUB_TOKEN environment variable
#   export GITHUB_TOKEN=ghp_your_token_here
#   bash scripts/push_to_github.sh
#
# Option 2: Use SSH (requires SSH key setup)
#   git remote set-url origin git@github.com:Ogienomo/havilah.git
#   bash scripts/push_to_github.sh

set -e
cd "$(dirname "$0")/.."

if [ -n "$GITHUB_TOKEN" ]; then
    echo "Using GITHUB_TOKEN for authentication..."
    git remote set-url origin "https://${GITHUB_TOKEN}@github.com/Ogienomo/havilah.git"
fi

echo "Pushing to GitHub..."
git push origin main

echo "Push complete!"
echo "View at: https://github.com/Ogienomo/havilah"
