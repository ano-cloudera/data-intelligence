#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-/home/cdsw}"
BRANCH="${2:-main}"

echo "[INFO] Starting FORCE repo sync"
echo "[INFO] Repo dir : ${REPO_DIR}"
echo "[INFO] Branch   : ${BRANCH}"

cd "${REPO_DIR}"

if [ ! -d ".git" ]; then
  echo "[ERROR] ${REPO_DIR} is not a git repository"
  exit 1
fi

echo "[INFO] Status before sync:"
git status --short || true

echo "[INFO] Fetching latest changes from origin"
git fetch origin

echo "[INFO] Checking out branch ${BRANCH}"
git checkout "${BRANCH}"

echo "[INFO] Resetting local branch to origin/${BRANCH}"
git reset --hard "origin/${BRANCH}"

echo "[INFO] Cleaning untracked files and directories"
git clean -fd

echo "[INFO] Current HEAD:"
git log --oneline -1

echo "[INFO] FORCE repo sync completed successfully"