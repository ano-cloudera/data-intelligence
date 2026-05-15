"""
CAI Application entry point for Qwen2.5 LLM served via vLLM.

This script is the Application script for the Qwen LLM CAI Application.
It launches vLLM as an OpenAI-compatible inference server.

Required env vars (set in CAI Application):
  QWEN_MODEL                  HuggingFace model ID (default: Qwen/Qwen2.5-14B-Instruct-AWQ)
  QWEN_API_KEY                API key for authentication (default: local-dev-token)
  QWEN_MAX_MODEL_LEN          Max context length in tokens (default: 8192)
  QWEN_GPU_MEMORY_UTILIZATION Fraction of GPU VRAM to use (default: 0.90)
  QWEN_TENSOR_PARALLEL_SIZE   Number of GPUs for tensor parallelism (default: 1)
  CDSW_APP_PORT / PORT        Port assigned by CAI (auto-detected)
"""

import logging
import os
import subprocess
import sys
from pathlib import Path


def resolve_port() -> int:
    raw_port = os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "8000"
    try:
        return int(raw_port)
    except ValueError:
        return 8000


def ensure_vllm_installed() -> None:
    try:
        import vllm  # noqa: F401
        logging.info("vLLM already installed.")
    except ImportError:
        logging.warning("vLLM not found. Installing from requirements.txt...")
        req_file = Path(__file__).parent / "requirements.txt"
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logging.info("Starting Qwen LLM Application (vLLM)")
    logging.info("Working directory: %s", Path.cwd())

    port = resolve_port()
    model = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-14B-Instruct-AWQ")
    api_key = os.getenv("QWEN_API_KEY", "local-dev-token")
    max_model_len = os.getenv("QWEN_MAX_MODEL_LEN", "8192")
    gpu_memory_utilization = os.getenv("QWEN_GPU_MEMORY_UTILIZATION", "0.90")
    tensor_parallel_size = os.getenv("QWEN_TENSOR_PARALLEL_SIZE", "1")

    logging.info("Model: %s", model)
    logging.info("Port: %s", port)
    logging.info("Max model len: %s", max_model_len)
    logging.info("GPU memory utilization: %s", gpu_memory_utilization)
    logging.info("Tensor parallel size: %s", tensor_parallel_size)

    ensure_vllm_installed()

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", model,
        "--host", "127.0.0.1",
        "--port", str(port),
        "--dtype", "auto",
        "--gpu-memory-utilization", gpu_memory_utilization,
        "--max-model-len", max_model_len,
        "--tensor-parallel-size", tensor_parallel_size,
        "--served-model-name", model,
        "--api-key", api_key,
        "--trust-remote-code",
    ]

    logging.info("Launching vLLM: %s", " ".join(cmd))

    env = os.environ.copy()
    process = subprocess.Popen(cmd, env=env)
    process.wait()

    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
