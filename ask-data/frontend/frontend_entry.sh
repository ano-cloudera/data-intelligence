#!/usr/bin/env sh
set -eu

if [ -z "${BACKEND_API_BASE_URL:-${NEXT_PUBLIC_API_BASE_URL:-}}" ]; then
  echo "BACKEND_API_BASE_URL or NEXT_PUBLIC_API_BASE_URL is required for frontend deployment." >&2
  exit 1
fi

export PORT="${CDSW_APP_PORT:-${PORT:-3000}}"

if [ ! -d node_modules ]; then
  npm install
fi

npm run build
npm run start
