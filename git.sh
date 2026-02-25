#!/bin/bash

# Navigate to project directory
cd green-fintech-baas/

# See all modified files
git status; sleep 2s

# Review the changes
git diff; sleep 2s

# Stage everything (both your original + fixed files)
git add .

SKIP=mypy git commit

git push origin
