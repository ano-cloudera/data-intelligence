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


def resolve_qwen_dir() -> Path:
    """Locate qwen_inference directory regardless of how the script is invoked."""
    # When run as a proper .py file
    try:
        return Path(__file__).parent
    except NameError:
        pass
    # When run as a Jupyter/CAI notebook cell — search from cwd
    cwd = Path.cwd()
    candidates = [
        cwd / "data-intelligence" / "ask-data" / "qwen_inference",
        cwd / "ask-data" / "qwen_inference",
        cwd / "qwen_inference",
    ]
    try:
        for entry in sorted(cwd.iterdir()):
            if entry.is_dir():
                candidates.append(entry / "ask-data" / "qwen_inference")
    except Exception:
        pass
    for c in candidates:
        if (c / "requirements.txt").exists():
            return c
    return cwd


MIN_VLLM_VERSION = (0, 7, 3)
MIN_TRANSFORMERS_VERSION = (4, 47, 0)


def _parse_version(version_str: str) -> tuple:
    parts = version_str.split(".")
    return tuple(int(p.split("post")[0].split("rc")[0]) for p in parts[:3])


def _vllm_version() -> tuple:
    try:
        import vllm
        return _parse_version(vllm.__version__)
    except Exception:
        return (0, 0, 0)


def _transformers_version() -> tuple:
    try:
        import transformers
        return _parse_version(transformers.__version__)
    except Exception:
        return (0, 0, 0)


def ensure_dependencies_installed() -> None:
    vllm_ver = _vllm_version()
    transformers_ver = _transformers_version()

    vllm_ok = vllm_ver >= MIN_VLLM_VERSION
    transformers_ok = transformers_ver >= MIN_TRANSFORMERS_VERSION

    logging.info(
        "vLLM: %s (required >=%s) — %s",
        ".".join(map(str, vllm_ver)),
        ".".join(map(str, MIN_VLLM_VERSION)),
        "OK" if vllm_ok else "UPGRADE NEEDED",
    )
    logging.info(
        "transformers: %s (required >=%s) — %s",
        ".".join(map(str, transformers_ver)),
        ".".join(map(str, MIN_TRANSFORMERS_VERSION)),
        "OK" if transformers_ok else "UPGRADE NEEDED",
    )

    if vllm_ok and transformers_ok:
        logging.info("All dependencies meet minimum requirements.")
        return

    req_file = resolve_qwen_dir() / "requirements.txt"
    if req_file.exists():
        logging.warning("Installing from requirements.txt (--upgrade to override system packages)...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "-r", str(req_file), "-q"],
            check=True,
        )
    else:
        logging.warning("requirements.txt not found, installing pinned versions directly...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade",
             "vllm==0.7.3", "torch==2.5.1", "transformers>=4.47.0", "-q"],
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

    ensure_dependencies_installed()

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
    # Disable flashinfer JIT compile — nvcc not available in CAI runtime
    env.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    # Suppress deprecation warnings from vLLM / transformers
    env.setdefault("PYTHONWARNINGS", "ignore::DeprecationWarning,ignore::UserWarning")
    # Prepend user site-packages so pip --upgrade packages override system /usr/local ones.
    # CAI GPU runtime has an old transformers in /usr/local that shadows ~/.local installs
    # when vLLM spawns child processes (SpawnProcess inherits sys.path from the OS, not
    # the running interpreter). Putting ~/.local first fixes the shadowing.
    import site
    user_site = site.getusersitepackages()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{user_site}:{existing_pythonpath}" if existing_pythonpath else user_site
    logging.info("PYTHONPATH set to: %s", env["PYTHONPATH"])

    process = subprocess.Popen(cmd, env=env)
    process.wait()

    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
