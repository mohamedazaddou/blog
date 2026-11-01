#!/usr/bin/env bash
# Récupère les flux, régénère le site, et pousse si un dépôt git existe.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/fetch.py
python3 scripts/build.py

if [ -d .git ]; then
  if ! git diff --quiet || [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -q -m "maj flux $(date -u +%Y-%m-%dT%H:%MZ)"
    git push -q 2>/dev/null || echo "push impossible (pas de remote configurée)"
    echo "commit créé"
  else
    echo "aucun changement"
  fi
fi
