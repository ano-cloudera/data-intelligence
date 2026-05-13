#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-/home/cdsw}"
BRANCH="${2:-main}"

echo "[INFO] Starting SAFE repo sync"
echo "[INFO] Repo dir : ${REPO_DIR}"
echo "[INFO] Branch   : ${BRANCH}"

cd "${REPO_DIR}"

if [ ! -d ".git" ]; then
  echo "[ERROR] ${REPO_DIR} is not a git repository"
  exit 1
fi

echo "[INFO] Removing lock files from git index if still tracked"
git rm --cached --quiet --ignore-unmatch \
  "ask-data/frontend/package-lock.json" \
  "healthcare/Xray Assistant/frontend/package-lock.json" || true

echo "[INFO] Checking tracked changes only"
TRACKED_CHANGES="$(git status --porcelain --untracked-files=no)"

if [ -n "${TRACKED_CHANGES}" ]; then
  echo "[ERROR] Tracked changes detected. Aborting sync."
  echo "[INFO] Pending tracked changes:"
  echo "${TRACKED_CHANGES}"
  exit 2
fi

echo "[INFO] Fetching latest changes from origin"
git fetch origin

echo "[INFO] Checking out branch ${BRANCH}"
git checkout "${BRANCH}"

echo "[INFO] Resetting local branch to origin/${BRANCH}"
git reset --hard "origin/${BRANCH}"

echo "[INFO] Current HEAD:"
git log --oneline -1

echo "[INFO] SAFE repo sync completed successfully"