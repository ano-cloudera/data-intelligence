#!/usr/bin/env bash
set -euo pipefail

export QWEN_MODEL="${QWEN_MODEL:-Qwen/Qwen3-8B-AWQ}"
export QWEN_API_KEY="${QWEN_API_KEY:-local-dev-token}"
export QWEN_PORT="${QWEN_PORT:-8000}"
export QWEN_MAX_MODEL_LEN="${QWEN_MAX_MODEL_LEN:-4096}"
export QWEN_GPU_MEMORY_UTILIZATION="${QWEN_GPU_MEMORY_UTILIZATION:-0.85}"

echo "Starting vLLM OpenAI-compatible server"
echo "Model: ${QWEN_MODEL}"
echo "Port : ${QWEN_PORT}"

vllm serve "${QWEN_MODEL}" \
  --host 0.0.0.0 \
  --port "${QWEN_PORT}" \
  --dtype auto \
  --gpu-memory-utilization "${QWEN_GPU_MEMORY_UTILIZATION}" \
  --max-model-len "${QWEN_MAX_MODEL_LEN}" \
  --served-model-name "${QWEN_MODEL}" \
  --api-key "${QWEN_API_KEY}"
