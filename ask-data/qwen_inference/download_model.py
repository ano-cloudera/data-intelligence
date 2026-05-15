"""
Download Qwen model to local cache before deploying the Qwen LLM Application.

Run this script in a Cloudera AI Workbench SESSION (not an Application) so the model
is cached at ~/.cache/huggingface before the Application starts.

Usage:
    python bank-jawa-timur/ask-data/qwen_inference/download_model.py

Required env var:
    HUGGING_FACE_HUB_TOKEN  — HuggingFace token with read access

Optional env vars:
    QWEN_MODEL              — model ID (default: Qwen/Qwen2.5-14B-Instruct-AWQ)
    HF_CACHE_DIR            — override cache dir (default: ~/.cache/huggingface/hub)
"""

import logging
import os
import subprocess
import sys
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def ensure_huggingface_hub() -> None:
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        log.info("Installing huggingface_hub...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "huggingface_hub>=0.24.0", "-q"],
            check=True,
        )


def download_model(model_id: str, token: str, cache_dir: str | None) -> None:
    from huggingface_hub import snapshot_download

    log.info("=" * 60)
    log.info("Model download: %s", model_id)
    log.info("Cache dir    : %s", cache_dir or "~/.cache/huggingface/hub (default)")
    log.info("=" * 60)

    kwargs: dict = {
        "repo_id": model_id,
        "token": token,
        "ignore_patterns": ["*.msgpack", "flax_model*", "tf_model*", "rust_model*"],
    }
    if cache_dir:
        kwargs["cache_dir"] = cache_dir

    local_dir = snapshot_download(**kwargs)
    log.info("Download complete. Local path: %s", local_dir)


def verify_cache(model_id: str, cache_dir: str | None) -> None:
    """Quick sanity-check: list files in the downloaded model dir."""
    from huggingface_hub import scan_cache_dir

    hf_cache = cache_dir or str(Path.home() / ".cache" / "huggingface" / "hub")
    log.info("Scanning HuggingFace cache at: %s", hf_cache)

    cache_info = scan_cache_dir(hf_cache)
    found = False
    for repo in cache_info.repos:
        if repo.repo_id == model_id:
            size_gb = repo.size_on_disk / (1024 ** 3)
            log.info("Found cached model: %s (%.2f GB, %d revision(s))", repo.repo_id, size_gb, len(repo.revisions))
            found = True
    if not found:
        log.warning("Model %s NOT found in cache — download may have failed.", model_id)


def main() -> None:
    token = os.getenv("HUGGING_FACE_HUB_TOKEN", "").strip()
    if not token:
        log.error("HUGGING_FACE_HUB_TOKEN is not set.")
        log.error("Set it as an env var in this Workbench session:")
        log.error("  export HUGGING_FACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxx")
        sys.exit(1)

    model_id = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-14B-Instruct-AWQ")
    cache_dir = os.getenv("HF_CACHE_DIR", "").strip() or None

    ensure_huggingface_hub()
    download_model(model_id, token, cache_dir)
    verify_cache(model_id, cache_dir)

    log.info("")
    log.info("Model ready. You can now deploy the Qwen LLM Application.")
    log.info("The Application will load from cache — no HF token needed at runtime.")


if __name__ == "__main__":
    main()
