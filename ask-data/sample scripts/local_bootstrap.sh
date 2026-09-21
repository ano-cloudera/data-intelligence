#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
pip install -r qwen_inference/requirements.txt

mkdir -p data
echo "Bootstrap complete."
echo "Next: bash qwen_inference/start_qwen_vllm.sh"
