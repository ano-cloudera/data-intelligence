"""
CAI Application entry point for Qwen2.5 LLM served via vLLM.

Launches vLLM as a subprocess on 127.0.0.1:CDSW_APP_PORT (default mode). CAI ingress
forwards to 127.0.0.1 — same bind host as launch_app.sh uses for uvicorn. The launcher
stays alive and forwards vLLM stdout/stderr to the Application logs (os.execve is not
used because CAI treats a replaced process as an engine exit).

Required env vars (set in CAI Application):
  QWEN_MODEL                  HuggingFace model ID (default: Qwen/Qwen2.5-14B-Instruct-AWQ)
  QWEN_API_KEY                API key for authentication (default: local-dev-token)
  QWEN_MAX_MODEL_LEN          Max context length in tokens (default: 8192)
  QWEN_GPU_MEMORY_UTILIZATION Fraction of GPU VRAM to use (default: 0.90)
  QWEN_TENSOR_PARALLEL_SIZE   Number of GPUs for tensor parallelism (default: 1)
  QWEN_INTERNAL_PORT          vLLM bind port (default: CDSW_APP_PORT + 10000)
  QWEN_USE_PROXY              Set to "true" to enable proxy mode (recommended)
  CDSW_APP_PORT / PORT        Port assigned by CAI (auto-detected)
"""

from __future__ import annotations

import http.client
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

DEPS_DIR = Path("/home/cdsw/.vllm_deps")
INTERNAL_PORT_OFFSET = 10_000
BIND_HOST = "127.0.0.1"
_PROXY_SERVER: ThreadingHTTPServer | None = None
_VLLM_PROCESS: subprocess.Popen | None = None


def resolve_port() -> int:
    raw_port = os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "8000"
    try:
        return int(raw_port)
    except ValueError:
        return 8000


def resolve_internal_port(app_port: int) -> int:
    raw = os.getenv("QWEN_INTERNAL_PORT")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return app_port + INTERNAL_PORT_OFFSET


def _parse_version(version_str: str) -> tuple[int, ...]:
    parts = version_str.split(".")
    return tuple(int(p.split("post")[0].split("rc")[0]) for p in parts[:3])


def _pkg_version(pkg: str) -> tuple[int, ...]:
    try:
        import importlib.metadata

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
    vllm_ok = vllm_ver >= (0, 7, 3)  # supports 0.7.3+ and 0.24+
    transformers_ok = transformers_ver >= (4, 47, 0)  # supports 4.x and 5.x
    logging.info(
        "vLLM in deps: %s — %s",
        ".".join(map(str, vllm_ver)),
        "OK" if vllm_ok else "INSTALL NEEDED",
    )
    logging.info(
        "transformers in deps: %s — %s",
        ".".join(map(str, transformers_ver)),
        "OK" if transformers_ok else "INSTALL NEEDED",
    )
    if vllm_ok and transformers_ok:
        logging.info("All pinned deps present in %s.", DEPS_DIR)
        return
    raise SystemExit(
        f"\n\n*** DEPS NOT READY in {DEPS_DIR} ***\n"
        "vLLM + transformers must be pre-installed in a Workbench session before starting this Application.\n"
        "Run in a Workbench terminal:\n\n"
        f"  PIP_USER=0 pip install --target {DEPS_DIR} \\\n"
        "    'vllm>=0.19.0' 'transformers>=5.5.4' \\\n"
        "    'tokenizers>=0.21.0' torch accelerate huggingface_hub -q\n\n"
        "Then restart this Application."
    )


def kill_pid(pid: int, my_pid: int) -> bool:
    if pid == my_pid:
        return False
    try:
        os.kill(pid, signal.SIGKILL)
        logging.info("Killed PID %d", pid)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def shutdown_existing_runtime() -> None:
    """Stop proxy/vLLM started by a prior main() in the same Workbench kernel."""
    global _PROXY_SERVER, _VLLM_PROCESS

    if _VLLM_PROCESS is not None and _VLLM_PROCESS.poll() is None:
        logging.info("Stopping prior vLLM subprocess (PID %d)", _VLLM_PROCESS.pid)
        _VLLM_PROCESS.kill()
        _VLLM_PROCESS.wait(timeout=10)
    _VLLM_PROCESS = None

    if _PROXY_SERVER is not None:
        logging.info("Stopping prior proxy server")
        _PROXY_SERVER.shutdown()
        _PROXY_SERVER.server_close()
        _PROXY_SERVER = None
        time.sleep(1)


def log_port_holder(port: int) -> None:
    for cmd in (
        ["ss", "-tlnp", f"sport = :{port}"],
        ["lsof", "-i", f":{port}"],
    ):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output = (result.stdout or result.stderr).strip()
            if output:
                logging.warning("Port %d holder (%s): %s", port, cmd[0], output)
        except FileNotFoundError:
            pass


def can_bind_port(port: int, host: str = BIND_HOST) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def build_vllm_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    env["PYTHONWARNINGS"] = "ignore::DeprecationWarning,ignore::UserWarning"
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{DEPS_DIR}:{existing_pythonpath}" if existing_pythonpath else str(DEPS_DIR)
    )
    return env


def free_port(port: int) -> None:
    """Kill any process holding the given TCP port."""
    my_pid = os.getpid()
    freed = False

    try:
        subprocess.run(
            ["fuser", "-k", "-9", f"{port}/tcp"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        freed = True
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["fuser", f"{port}/tcp"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for pid_str in result.stdout.strip().split():
            try:
                if kill_pid(int(pid_str), my_pid):
                    freed = True
            except ValueError:
                pass
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["ss", "-tlnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for token in result.stdout.split():
            if "pid=" in token:
                pid_str = token.split("pid=")[1].split(",")[0]
                try:
                    if kill_pid(int(pid_str), my_pid):
                        freed = True
                except ValueError:
                    pass
    except FileNotFoundError:
        pass

    try:
        hex_port = f"{port:04X}"
        with open("/proc/net/tcp") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 10:
                    continue
                local_addr = parts[1]
                if local_addr.split(":")[1].upper() != hex_port:
                    continue
                inode = parts[9]
                for pid_dir in Path("/proc").iterdir():
                    if not pid_dir.name.isdigit():
                        continue
                    pid = int(pid_dir.name)
                    try:
                        fd_dir = pid_dir / "fd"
                        for fd in fd_dir.iterdir():
                            if fd.is_symlink() and f"socket:[{inode}]" in str(fd.resolve()):
                                if kill_pid(pid, my_pid):
                                    freed = True
                    except (PermissionError, FileNotFoundError):
                        pass
    except Exception:
        pass

    if freed:
        time.sleep(2)
        logging.info("Port %d cleared.", port)
    else:
        logging.info("Port %d — no conflicting process found.", port)


def ensure_port_available(port: int, host: str = BIND_HOST, retries: int = 5) -> None:
    for attempt in range(1, retries + 1):
        free_port(port)
        if can_bind_port(port, host):
            return
        logging.warning(
            "Port %s:%d still busy (attempt %d/%d)",
            host,
            port,
            attempt,
            retries,
        )
        log_port_holder(port)
        time.sleep(3)
    log_port_holder(port)
    raise SystemExit(
        f"Port {host}:{port} is still in use after {retries} cleanup attempts.\n"
        "1. Stop the CAI Application completely.\n"
        "2. Restart the Workbench kernel if you tested via notebook cells.\n"
        "3. In a Workbench terminal run:\n"
        f"     pkill -f vllm.entrypoints.openai.api_server\n"
        f"     fuser -k {port}/tcp\n"
        "4. Start the Application again (do not re-run main() in the same kernel)."
    )


def kill_stale_vllm() -> None:
    """Stop leftover vLLM workers from prior app runs."""
    patterns = [
        "vllm.entrypoints.openai.api_server",
        "vllm.engine",
    ]
    my_pid = os.getpid()
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for pid_str in result.stdout.strip().split():
                try:
                    kill_pid(int(pid_str), my_pid)
                except ValueError:
                    pass
        except FileNotFoundError:
            pass
    time.sleep(2)


def wait_for_vllm(port: int, api_key: str, timeout_s: int = 900) -> bool:
    """Poll /v1/models until vLLM is ready or timeout."""
    deadline = time.time() + timeout_s
    headers = {"Authorization": f"Bearer {api_key}"}
    while time.time() < deadline:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/v1/models", headers=headers)
            resp = conn.getresponse()
            resp.read()
            conn.close()
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def make_handler(
    *,
    app_port: int,
    internal_port: int,
    is_ready: Callable[[], bool],
) -> type[BaseHTTPRequestHandler]:
    class ProxyHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            logging.debug("proxy %s", fmt % args)

        def _send_loading(self) -> None:
            body = b'{"status":"loading","message":"Qwen model is loading; retry shortly."}'
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _proxy(self, method: str) -> None:
            if not is_ready():
                self._send_loading()
                return

            content_length = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(content_length) if content_length else None
            headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}

            conn = http.client.HTTPConnection("127.0.0.1", internal_port, timeout=600)
            try:
                conn.request(method, self.path, body=body, headers=headers)
                resp = conn.getresponse()
                self.send_response(resp.status)
                for header, value in resp.getheaders():
                    if header.lower() == "transfer-encoding":
                        continue
                    self.send_header(header, value)
                self.end_headers()
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            finally:
                conn.close()

        def do_GET(self) -> None:
            self._proxy("GET")

        def do_POST(self) -> None:
            self._proxy("POST")

        def do_PUT(self) -> None:
            self._proxy("PUT")

        def do_DELETE(self) -> None:
            self._proxy("DELETE")

        def do_OPTIONS(self) -> None:
            self._proxy("OPTIONS")

    return ProxyHandler


class ReuseThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    allow_reuse_port = True


def start_proxy(
    *,
    app_port: int,
    internal_port: int,
    is_ready: Callable[[], bool],
) -> ReuseThreadingHTTPServer:
    global _PROXY_SERVER

    handler = make_handler(
        app_port=app_port,
        internal_port=internal_port,
        is_ready=is_ready,
    )
    server = ReuseThreadingHTTPServer((BIND_HOST, app_port), handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    _PROXY_SERVER = server
    logging.info(
        "Proxy listening on %s:%d (returns 503 until model is ready)",
        BIND_HOST,
        app_port,
    )
    return server


def build_vllm_cmd(
    *,
    model: str,
    host: str,
    port: int,
    api_key: str,
    max_model_len: str,
    gpu_memory_utilization: str,
    tensor_parallel_size: str,
) -> list[str]:
    tool_call_parser = "pythonic" if "qwen3" in model.lower() else "hermes"
    return [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model", model,
        "--host", host,
        "--port", str(port),
        "--dtype", "auto",
        "--gpu-memory-utilization", gpu_memory_utilization,
        "--max-model-len", max_model_len,
        "--tensor-parallel-size", tensor_parallel_size,
        "--served-model-name", model,
        "--api-key", api_key,
        "--trust-remote-code",
        "--enable-auto-tool-choice",
        "--tool-call-parser", tool_call_parser,
    ]


def preflight_vllm() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import vllm; print(vllm.__version__)"],
        env=build_vllm_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        logging.error("vLLM preflight import failed (exit %d)", result.returncode)
        if result.stdout.strip():
            logging.error("stdout: %s", result.stdout.strip())
        if result.stderr.strip():
            logging.error("stderr: %s", result.stderr.strip())
        raise SystemExit(result.returncode)
    logging.info("vLLM preflight OK (version %s)", result.stdout.strip())


def launch_vllm(cmd: list[str]) -> subprocess.Popen:
    global _VLLM_PROCESS

    logging.info("Launching vLLM: %s", " ".join(cmd))
    _VLLM_PROCESS = subprocess.Popen(
        cmd,
        env=build_vllm_env(),
        stdout=None,
        stderr=None,
    )
    return _VLLM_PROCESS


def run_direct_vllm(
    *,
    app_port: int,
    model: str,
    api_key: str,
    max_model_len: str,
    gpu_memory_utilization: str,
    tensor_parallel_size: str,
) -> None:
    preflight_vllm()
    cmd = build_vllm_cmd(
        model=model,
        host=BIND_HOST,
        port=app_port,
        api_key=api_key,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        tensor_parallel_size=tensor_parallel_size,
    )
    logging.info("Starting vLLM on %s:%d (subprocess)", BIND_HOST, app_port)
    exit_code = subprocess.call(cmd, env=build_vllm_env())
    if exit_code != 0:
        logging.error(
            "vLLM exited with code %d. Check GPU profile, VRAM, and model ID.",
            exit_code,
        )
    raise SystemExit(exit_code)


def run_proxy_vllm(
    *,
    app_port: int,
    internal_port: int,
    model: str,
    api_key: str,
    max_model_len: str,
    gpu_memory_utilization: str,
    tensor_parallel_size: str,
) -> None:
    ready = {"value": False}
    ensure_port_available(app_port)
    ensure_port_available(internal_port)
    start_proxy(
        app_port=app_port,
        internal_port=internal_port,
        is_ready=lambda: ready["value"],
    )

    cmd = build_vllm_cmd(
        model=model,
        host=BIND_HOST,
        port=internal_port,
        api_key=api_key,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        tensor_parallel_size=tensor_parallel_size,
    )
    process = launch_vllm(cmd)

    if not wait_for_vllm(internal_port, api_key):
        process.kill()
        raise SystemExit("vLLM did not become ready before timeout")

    ready["value"] = True
    logging.info(
        "vLLM ready — proxying %s:%d -> %s:%d",
        BIND_HOST, app_port, BIND_HOST, internal_port,
    )
    raise SystemExit(process.wait())


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("Starting Qwen LLM Application (vLLM)")
    logging.info("Working directory: %s", Path.cwd())

    app_port = resolve_port()
    internal_port = resolve_internal_port(app_port)
    model = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-14B-Instruct-AWQ")
    api_key = os.getenv("QWEN_API_KEY", "local-dev-token")
    max_model_len = os.getenv("QWEN_MAX_MODEL_LEN", "8192")
    gpu_memory_utilization = os.getenv("QWEN_GPU_MEMORY_UTILIZATION", "0.90")
    tensor_parallel_size = os.getenv("QWEN_TENSOR_PARALLEL_SIZE", "1")
    use_proxy = os.getenv("QWEN_USE_PROXY", "").lower() in ("1", "true", "yes")

    logging.info("Model: %s", model)
    logging.info("App port: %s", app_port)
    logging.info("Bind host: %s", BIND_HOST)
    logging.info("Mode: %s", "proxy" if use_proxy else "direct (subprocess)")
    if use_proxy:
        logging.info("Internal vLLM port: %s", internal_port)
    logging.info("Max model len: %s", max_model_len)
    logging.info("GPU memory utilization: %s", gpu_memory_utilization)
    logging.info("Tensor parallel size: %s", tensor_parallel_size)

    ensure_deps_installed()
    shutdown_existing_runtime()
    kill_stale_vllm()
    free_port(app_port)
    if use_proxy:
        free_port(internal_port)
    time.sleep(2)

    common = {
        "app_port": app_port,
        "model": model,
        "api_key": api_key,
        "max_model_len": max_model_len,
        "gpu_memory_utilization": gpu_memory_utilization,
        "tensor_parallel_size": tensor_parallel_size,
    }

    if use_proxy:
        run_proxy_vllm(internal_port=internal_port, **common)
    run_direct_vllm(**common)


if __name__ == "__main__":
    main()
