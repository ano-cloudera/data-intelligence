import os
import sys
import time
import hashlib
import subprocess
from pathlib import Path

import requests


# =========================================================
# CONFIGURATION
# =========================================================

def _resolve_base_dir() -> Path:
    """Locate the vllm/ directory this file lives in.

    CAI can execute an Application's script as interpreter/notebook code
    (shown as "Cell In[N]" in the logs), where __file__ is not defined at
    all — so we can't just trust Path(__file__) like a normal script.
    Fall back to CDSW_PROJECT_DIR / cwd and search for a "vllm" folder
    that actually contains this app's files.
    """
    script_path = globals().get("__file__")
    if script_path:
        return Path(script_path).resolve().parent

    cwd = Path.cwd().resolve()
    project_dir_env = os.getenv("CDSW_PROJECT_DIR")
    candidates = ([Path(project_dir_env).resolve()] if project_dir_env else []) + [cwd]

    for base in candidates:
        for candidate in (base / "vllm", base):
            if (candidate / "app.py").is_file() and (candidate / "proxy.py").is_file():
                return candidate
        for candidate in base.glob("*/vllm"):
            if (candidate / "app.py").is_file() and (candidate / "proxy.py").is_file():
                return candidate

    raise RuntimeError(
        "Unable to locate the vllm/ application directory. "
        "Set CDSW_PROJECT_DIR or start this Application from the project root."
    )


# Auto-detect: this file lives at <repo>/vllm/app.py, so the repo root
# is always this file's grandparent — no need to hardcode the CAI project
# folder name (it can change per clone/project).
BASE_DIR = _resolve_base_dir()

PROJECT_DIR = BASE_DIR.parent

VENV_DIR = PROJECT_DIR / ".venv"

PYTHON_BIN = VENV_DIR / "bin" / "python"
VLLM_BIN = VENV_DIR / "bin" / "vllm"

REQUIREMENTS_FILE = (
    BASE_DIR / "requirements.txt"
)

REQUIREMENTS_HASH_FILE = (
    VENV_DIR / ".requirements_hash"
)


# =========================================================
# MODEL
# =========================================================

MODEL_DIR = os.getenv(
    "MODEL_DIR",
    "/home/cdsw/models/Qwen3.5-9B"
)


# =========================================================
# PORTS
# =========================================================

APP_PORT = (
    os.getenv("CDSW_READONLY_PORT")
    or os.getenv("CDSW_APP_PORT")
)


VLLM_PORT = os.getenv(
    "VLLM_INTERNAL_PORT",
    "9000"
)


# =========================================================
# vLLM SETTINGS
# =========================================================

MAX_WAIT_SECONDS = int(
    os.getenv(
        "VLLM_STARTUP_TIMEOUT",
        "1200"
    )
)


VLLM_MAX_MODEL_LEN = os.getenv(
    "VLLM_MAX_MODEL_LEN",
    "4096"
)


VLLM_GPU_MEMORY_UTILIZATION = os.getenv(
    "VLLM_GPU_MEMORY_UTILIZATION",
    "0.90"
)


VLLM_MAX_NUM_SEQS = os.getenv(
    "VLLM_MAX_NUM_SEQS",
    "2"
)


# Qwen3 / Qwen3.5 default to "thinking" mode (long <think>...</think>
# reasoning block prepended to every response). Default this OFF for speed
# and to avoid leaking raw chain-of-thought; override via CAI Application
# env var VLLM_ENABLE_THINKING=true if a caller genuinely needs it.
VLLM_ENABLE_THINKING = os.getenv(
    "VLLM_ENABLE_THINKING",
    "false"
).strip().lower() in ("1", "true", "yes")


# =========================================================
# VALIDATION
# =========================================================

if not APP_PORT:

    raise RuntimeError(
        "CDSW_READONLY_PORT / "
        "CDSW_APP_PORT not found."
    )


if not PROJECT_DIR.exists():

    raise RuntimeError(
        f"Project directory not found: "
        f"{PROJECT_DIR}"
    )


if not BASE_DIR.exists():

    raise RuntimeError(
        f"vLLM directory not found: "
        f"{BASE_DIR}"
    )


if not REQUIREMENTS_FILE.exists():

    raise RuntimeError(
        f"requirements.txt not found: "
        f"{REQUIREMENTS_FILE}"
    )


if not Path(MODEL_DIR).exists():

    raise RuntimeError(
        f"Model directory not found: "
        f"{MODEL_DIR}"
    )


os.chdir(
    BASE_DIR
)


sys.path.insert(
    0,
    str(BASE_DIR)
)


# =========================================================
# HELPER
# =========================================================

def calculate_file_hash(
    path: Path
) -> str:

    sha256 = hashlib.sha256()

    with open(
        path,
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b""
        ):

            sha256.update(
                chunk
            )

    return sha256.hexdigest()


# =========================================================
# STARTUP INFO
# =========================================================

print("=" * 70)
print("QWEN3.5-9B vLLM APPLICATION")
print("=" * 70)

print(
    "Project directory      :",
    PROJECT_DIR
)

print(
    "Working directory      :",
    BASE_DIR
)

print(
    "Model directory        :",
    MODEL_DIR
)

print(
    "Virtual environment    :",
    VENV_DIR
)

print(
    "Application port       :",
    APP_PORT
)

print(
    "vLLM internal port     :",
    VLLM_PORT
)

print(
    "Max model length       :",
    VLLM_MAX_MODEL_LEN
)

print(
    "GPU memory utilization :",
    VLLM_GPU_MEMORY_UTILIZATION
)

print(
    "Max num sequences      :",
    VLLM_MAX_NUM_SEQS
)

print(
    "Thinking mode enabled  :",
    VLLM_ENABLE_THINKING
)

print("=" * 70)
print()


# =========================================================
# CREATE VENV
# =========================================================

if not PYTHON_BIN.exists():

    print("=" * 70)
    print("CREATING VIRTUAL ENVIRONMENT")
    print("=" * 70)


    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "venv",
            str(VENV_DIR)
        ]
    )


    print(
        "Virtual environment created:",
        VENV_DIR
    )

else:

    print(
        "Using existing virtual environment:",
        VENV_DIR
    )


print()


# =========================================================
# CLEAN PIP ENVIRONMENT
# =========================================================

pip_env = os.environ.copy()


pip_env.pop(
    "PIP_USER",
    None
)

pip_env.pop(
    "PYTHONUSERBASE",
    None
)


pip_env[
    "PIP_CONFIG_FILE"
] = os.devnull


pip_env[
    "PYTHONNOUSERSITE"
] = "1"


pip_env[
    "VIRTUAL_ENV"
] = str(
    VENV_DIR
)


pip_env[
    "PATH"
] = (
    f"{VENV_DIR / 'bin'}:"
    f"{pip_env.get('PATH', '')}"
)


# =========================================================
# PREPARE PIP
# =========================================================

print("=" * 70)
print("PREPARING VIRTUAL ENVIRONMENT")
print("=" * 70)


subprocess.check_call(
    [
        str(PYTHON_BIN),
        "-m",
        "pip",
        "--isolated",
        "install",
        "--upgrade",
        "pip",
        "setuptools",
        "wheel"
    ],
    env=pip_env
)


# =========================================================
# REQUIREMENTS HASH
# =========================================================

current_hash = (
    calculate_file_hash(
        REQUIREMENTS_FILE
    )
)


installed_hash = None


if REQUIREMENTS_HASH_FILE.exists():

    installed_hash = (
        REQUIREMENTS_HASH_FILE
        .read_text()
        .strip()
    )


# =========================================================
# INSTALL DEPENDENCIES
# =========================================================

if current_hash != installed_hash:

    print()
    print("=" * 70)
    print("INSTALLING DEPENDENCIES")
    print("=" * 70)


    subprocess.check_call(
        [
            str(PYTHON_BIN),
            "-m",
            "pip",
            "--isolated",
            "install",
            "--no-cache-dir",
            "-r",
            str(REQUIREMENTS_FILE)
        ],
        env=pip_env
    )


    REQUIREMENTS_HASH_FILE.write_text(
        current_hash
    )

else:

    print()
    print(
        "Requirements unchanged."
    )

    print(
        "Skipping dependency installation."
    )


# =========================================================
# VALIDATE ENV
# =========================================================

print()
print("=" * 70)
print("VALIDATING ENVIRONMENT")
print("=" * 70)


subprocess.check_call(
    [
        str(PYTHON_BIN),
        "-c",
        (
            "import sys; "
            "import torch; "
            "import openai; "
            "import vllm; "
            "print('Python:', sys.executable); "
            "print('Torch:', torch.__version__); "
            "print('CUDA:', torch.version.cuda); "
            "print('CUDA available:', torch.cuda.is_available()); "
            "print('OpenAI:', openai.__version__); "
            "print('vLLM:', vllm.__version__)"
        )
    ],
    env=pip_env
)


if not VLLM_BIN.exists():

    raise RuntimeError(
        f"vLLM binary not found: "
        f"{VLLM_BIN}"
    )


# =========================================================
# RUNTIME ENV
# =========================================================

vllm_env = (
    os.environ.copy()
)


vllm_env.pop(
    "PIP_USER",
    None
)

vllm_env.pop(
    "PYTHONUSERBASE",
    None
)


vllm_env[
    "PYTHONNOUSERSITE"
] = "1"


vllm_env[
    "VIRTUAL_ENV"
] = str(
    VENV_DIR
)


vllm_env[
    "PATH"
] = (
    f"{VENV_DIR / 'bin'}:"
    f"{vllm_env.get('PATH', '')}"
)


vllm_env[
    "PYTORCH_CUDA_ALLOC_CONF"
] = (
    "expandable_segments:True"
)


vllm_env[
    "VLLM_USE_FLASHINFER_SAMPLER"
] = "0"


# =========================================================
# vLLM COMMAND
# =========================================================

vllm_cmd = [
    str(VLLM_BIN),

    "serve",

    MODEL_DIR,

    "--host",
    "127.0.0.1",

    "--port",
    str(VLLM_PORT),

    "--max-model-len",
    str(
        VLLM_MAX_MODEL_LEN
    ),

    "--gpu-memory-utilization",
    str(
        VLLM_GPU_MEMORY_UTILIZATION
    ),

    "--max-num-seqs",
    str(
        VLLM_MAX_NUM_SEQS
    ),

    "--language-model-only",

    "--enforce-eager",

    "--trust-remote-code",

    # Server-side default; a caller can still opt back in per-request by
    # sending chat_template_kwargs.enable_thinking=true on its own request.
    "--chat-template-kwargs",
    (
        '{"enable_thinking": true}'
        if VLLM_ENABLE_THINKING
        else '{"enable_thinking": false}'
    ),
]


print()
print("=" * 70)
print("STARTING QWEN3.5-9B WITH vLLM")
print("=" * 70)

print(
    " ".join(
        vllm_cmd
    )
)

print()


# =========================================================
# START vLLM
# =========================================================

vllm_process = (
    subprocess.Popen(
        vllm_cmd,
        cwd=str(
            BASE_DIR
        ),
        env=vllm_env
    )
)


print(
    "vLLM PID:",
    vllm_process.pid
)


# =========================================================
# WAIT FOR API
# =========================================================

MODELS_URL = (
    f"http://127.0.0.1:"
    f"{VLLM_PORT}/v1/models"
)


print()
print("=" * 70)
print("WAITING FOR vLLM")
print("=" * 70)


start_time = (
    time.time()
)


while True:

    elapsed = int(
        time.time()
        - start_time
    )


    return_code = (
        vllm_process.poll()
    )


    if return_code is not None:

        raise RuntimeError(
            "vLLM exited during startup "
            f"with code {return_code}"
        )


    try:

        response = requests.get(
            MODELS_URL,
            timeout=10
        )


        print(
            f"[{elapsed}s] "
            f"/v1/models -> "
            f"HTTP {response.status_code}"
        )


        if (
            response.status_code
            == 200
        ):

            print()
            print("=" * 70)
            print("vLLM READY")
            print("=" * 70)

            print(
                response.text[:2000]
            )

            print()

            break


    except requests.RequestException:

        print(
            f"[{elapsed}s] "
            "vLLM still starting..."
        )


    if elapsed >= MAX_WAIT_SECONDS:

        if (
            vllm_process.poll()
            is None
        ):

            vllm_process.terminate()


        raise RuntimeError(
            "vLLM startup timeout after "
            f"{MAX_WAIT_SECONDS} seconds."
        )


    time.sleep(
        5
    )


# =========================================================
# START FASTAPI PROXY
# =========================================================

proxy_cmd = [
    str(PYTHON_BIN),

    "-m",
    "uvicorn",

    "proxy:app",

    "--host",
    "127.0.0.1",

    "--port",
    str(APP_PORT),

    "--app-dir",
    str(BASE_DIR),

    "--log-level",
    "info"
]


print("=" * 70)
print("STARTING CAI PROXY")
print("=" * 70)

print(
    " ".join(
        proxy_cmd
    )
)

print()


proxy_process = (
    subprocess.Popen(
        proxy_cmd,
        cwd=str(
            BASE_DIR
        ),
        env=vllm_env
    )
)


print(
    "Proxy PID:",
    proxy_process.pid
)


# =========================================================
# KEEP ALIVE
# =========================================================

try:

    while True:

        proxy_return = (
            proxy_process.poll()
        )

        vllm_return = (
            vllm_process.poll()
        )


        if proxy_return is not None:

            raise RuntimeError(
                "Proxy exited with code "
                f"{proxy_return}"
            )


        if vllm_return is not None:

            raise RuntimeError(
                "vLLM exited with code "
                f"{vllm_return}"
            )


        time.sleep(
            5
        )


except KeyboardInterrupt:

    print(
        "Application interrupted."
    )


finally:

    print()
    print("=" * 70)
    print("STOPPING APPLICATION")
    print("=" * 70)


    if (
        "proxy_process" in locals()
        and
        proxy_process.poll() is None
    ):

        proxy_process.terminate()

        try:

            proxy_process.wait(
                timeout=10
            )

        except subprocess.TimeoutExpired:

            proxy_process.kill()


    if (
        "vllm_process" in locals()
        and
        vllm_process.poll() is None
    ):

        vllm_process.terminate()

        try:

            vllm_process.wait(
                timeout=30
            )

        except subprocess.TimeoutExpired:

            vllm_process.kill()


    print(
        "Application stopped."
    )