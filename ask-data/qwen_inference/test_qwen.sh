#!/usr/bin/env bash
set -euo pipefail

QWEN_BASE_URL="${QWEN_BASE_URL:-http://localhost:8000/v1}"
QWEN_API_KEY="${QWEN_API_KEY:-local-dev-token}"
QWEN_MODEL="${QWEN_MODEL:-Qwen/Qwen3-8B-AWQ}"

curl "${QWEN_BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${QWEN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${QWEN_MODEL}\",
    \"messages\": [
      {
        \"role\": \"system\",
        \"content\": \"Anda adalah assistant analitik perbankan. Jawab dalam Bahasa Indonesia.\"
      },
      {
        \"role\": \"user\",
        \"content\": \"Jelaskan fungsi customer segmentation untuk bank dalam 2 kalimat.\"
      }
    ],
    \"temperature\": 0.2,
    \"max_tokens\": 300
  }"
