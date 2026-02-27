#!/bin/bash

# Navigate to project directory
cd ~/github-projects/uni/sem2/comp3011/green-fintech-baas/

# See all modified files
git status; sleep 2s

# Review the changes
git diff

# Stage everything (both your original + fixed files)
git add .

SKIP=mypy git commit

git push origin
