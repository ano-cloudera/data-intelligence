"""
CAI Application entry point for Qwen2.5/Qwen3 LLM served via vLLM.

Architecture:
  Internet → [CAI public port] → [Proxy :public_port] → [vLLM :vllm_port]

The proxy sits in front of vLLM and normalizes all requests so ANY app
(Agent Studio, Ask-Data, custom apps) can use it as a drop-in OpenAI
replacement without Qwen-specific client code.

Required env vars (set in CAI Application):
  QWEN_MODEL                  HuggingFace model ID (default: Qwen/Qwen2.5-14B-Instruct-AWQ)
  QWEN_API_KEY                API key for authentication (default: local-dev-token)
  QWEN_MAX_MODEL_LEN          Max context length in tokens (default: 4096)
  QWEN_GPU_MEMORY_UTILIZATION Fraction of GPU VRAM to use (default: 0.90)
  QWEN_TENSOR_PARALLEL_SIZE   Number of GPUs for tensor parallelism (default: 1)
  QWEN_VLLM_INTERNAL_PORT     Internal vLLM port, default 8001 (not exposed)
  CDSW_APP_PORT / PORT        Public port assigned by CAI (proxy listens here)
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


# Isolated deps dir — installed here take absolute priority over system and user site-packages.
# This avoids transformers 5.x (installed system-wide) shadowing the pinned 4.x we need.
DEPS_DIR = Path("/home/cdsw/.vllm_deps")

PINNED_PACKAGES = [
    "vllm==0.7.3",
    "torch==2.5.1",
    "transformers==4.51.3",
    "tokenizers>=0.19.0,<0.22",
    "accelerate>=0.34.0",
    "huggingface_hub>=0.24.0",
]


def _parse_version(version_str: str) -> tuple:
    parts = version_str.split(".")
    return tuple(int(p.split("post")[0].split("rc")[0]) for p in parts[:3])


def _pkg_version(pkg: str) -> tuple:
    """Return installed version tuple from DEPS_DIR, or (0,0,0) if missing."""
    try:
        import importlib.metadata
        # Temporarily add DEPS_DIR to find packages installed there
        sys.path.insert(0, str(DEPS_DIR))
        ver = importlib.metadata.version(pkg)
        sys.path.pop(0)
        return _parse_version(ver)
    except Exception:
        return (0, 0, 0)


def ensure_deps_installed() -> None:
    DEPS_DIR.mkdir(parents=True, exist_ok=True)

    vllm_ver = _pkg_version("vllm")
    transformers_ver = _pkg_version("transformers")

    vllm_ok = vllm_ver >= (0, 7, 3)
    # transformers must be 4.x — 5.x removed all_special_tokens_extended
    transformers_ok = (4, 47, 0) <= transformers_ver < (5, 0, 0)

    logging.info("vLLM in deps: %s — %s", ".".join(map(str, vllm_ver)), "OK" if vllm_ok else "INSTALL NEEDED")
    logging.info("transformers in deps: %s — %s", ".".join(map(str, transformers_ver)), "OK" if transformers_ok else "INSTALL NEEDED")

    if vllm_ok and transformers_ok:
        logging.info("All pinned deps present in %s.", DEPS_DIR)
        return

    # Installing torch + vllm inside Application OOMs on 8 GiB RAM (exit 137).
    # Run this manually in a Workbench session before deploying:
    #   PIP_USER=0 pip install --target /home/cdsw/.vllm_deps \
    #     vllm==0.7.3 torch==2.5.1 "transformers==4.51.3" \
    #     "tokenizers>=0.19.0,<0.22" accelerate huggingface_hub -q
    raise SystemExit(
        f"\n\n*** DEPS NOT READY in {DEPS_DIR} ***\n"
        "vLLM + transformers must be pre-installed in a Workbench session before starting this Application.\n"
        "Run in a Workbench terminal:\n\n"
        f"  PIP_USER=0 pip install --target {DEPS_DIR} \\\n"
        "    vllm==0.7.3 torch==2.5.1 'transformers==4.51.3' \\\n"
        "    'tokenizers>=0.19.0,<0.22' accelerate huggingface_hub -q\n\n"
        "Then restart this Application."
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logging.info("Starting Qwen LLM Application (vLLM)")
    logging.info("Working directory: %s", Path.cwd())

    port                   = resolve_port()
    model                  = os.getenv("QWEN_MODEL",                    "Qwen/Qwen2.5-14B-Instruct-AWQ")
    api_key                = os.getenv("QWEN_API_KEY",                  "local-dev-token")
    max_model_len          = os.getenv("QWEN_MAX_MODEL_LEN",            "4096")
    gpu_memory_utilization = os.getenv("QWEN_GPU_MEMORY_UTILIZATION",   "0.90")
    tensor_parallel_size   = os.getenv("QWEN_TENSOR_PARALLEL_SIZE",     "1")

    logging.info("Model : %s", model)
    logging.info("Port  : %d", port)

    ensure_deps_installed()

    is_qwen3 = "qwen3" in model.lower()
    tool_call_parser = "pythonic" if is_qwen3 else "hermes"

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", model,
        "--host", "0.0.0.0",
        "--port", str(port),
        "--dtype", "auto",
        "--gpu-memory-utilization", gpu_memory_utilization,
        "--max-model-len", max_model_len,
        "--tensor-parallel-size", tensor_parallel_size,
        "--served-model-name", model,
        "--api-key", api_key,
        "--trust-remote-code",
        "--enforce-eager",
        "--enable-auto-tool-choice",
        "--tool-call-parser", tool_call_parser,
    ]

    qwen_dir = resolve_qwen_dir()
    template_path = qwen_dir / (
        "qwen3_no_think_template.jinja" if is_qwen3 else "qwen25_crewai_template.jinja"
    )
    if template_path.exists():
        cmd += ["--chat-template", str(template_path)]
        logging.info("Chat template: %s", template_path)
    else:
        logging.warning("Chat template not found at %s", template_path)

    logging.info("Launching vLLM: %s", " ".join(cmd))

    env = os.environ.copy()
    env.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    env["PYTHONWARNINGS"] = "ignore::DeprecationWarning,ignore::UserWarning"
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{DEPS_DIR}:{existing_pythonpath}" if existing_pythonpath else str(DEPS_DIR)

    process = subprocess.Popen(cmd, env=env)
    process.wait()

    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
