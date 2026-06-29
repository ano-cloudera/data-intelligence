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

# Select tool-call parser: Qwen3 uses "pythonic", Qwen2.5 uses "hermes"
if echo "${QWEN_MODEL}" | grep -qi "qwen3"; then
  TOOL_CALL_PARSER="pythonic"
  IS_QWEN3=true
else
  TOOL_CALL_PARSER="hermes"
  IS_QWEN3=false
fi
echo "Tool-call parser: ${TOOL_CALL_PARSER}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_ARG=""
if [ "${IS_QWEN3}" = true ]; then
  TEMPLATE_FILE="${SCRIPT_DIR}/qwen3_no_think_template.jinja"
  if [ -f "${TEMPLATE_FILE}" ]; then
    TEMPLATE_ARG="--chat-template ${TEMPLATE_FILE}"
    echo "Qwen3: using no-think chat template → ${TEMPLATE_FILE}"
  else
    echo "WARNING: Qwen3 no-think template not found at ${TEMPLATE_FILE}"
  fi
fi

vllm serve "${QWEN_MODEL}" \
  --host 0.0.0.0 \
  --port "${QWEN_PORT}" \
  --dtype auto \
  --gpu-memory-utilization "${QWEN_GPU_MEMORY_UTILIZATION}" \
  --max-model-len "${QWEN_MAX_MODEL_LEN}" \
  --served-model-name "${QWEN_MODEL}" \
  --api-key "${QWEN_API_KEY}" \
  --enable-auto-tool-choice \
  --tool-call-parser "${TOOL_CALL_PARSER}" \
  ${TEMPLATE_ARG}
