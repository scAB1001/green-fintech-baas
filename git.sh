#!/bin/bash

cd green-fintech-baas/

git status; sleep 2s

git add .

SKIP=black,reorder-python-imports,double-quote-string-fixer git commit

git push origin chore/setup-python-poetry
