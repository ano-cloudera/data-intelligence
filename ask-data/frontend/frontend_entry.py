import logging
import os
import shutil
import subprocess
from pathlib import Path


def resolve_port() -> int:
    raw_port = os.getenv("PORT") or os.getenv("CDSW_APP_PORT") or "3000"
    try:
        return int(raw_port)
    except ValueError:
        return 3000


def resolve_frontend_dir() -> Path:
    cwd = Path.cwd()

    # Dump env vars and cwd listing to help diagnose path issues in CAI
    cdsw_vars = {k: v for k, v in os.environ.items() if "CDSW" in k or "CML" in k}
    logging.info("CAI env vars: %s", cdsw_vars)

    try:
        top_level = sorted(str(p) for p in cwd.iterdir())
        logging.info("Contents of cwd (%s): %s", cwd, top_level)
    except Exception as exc:
        logging.warning("Could not list cwd: %s", exc)

    candidates: list[Path] = [
        cwd / "data-intelligence" / "ask-data" / "frontend",
        cwd / "ask-data" / "frontend",
        cwd / "frontend",
    ]

    # Scan one level deep under cwd
    try:
        for entry in sorted(cwd.iterdir()):
            if entry.is_dir():
                candidates.append(entry / "ask-data" / "frontend")
                candidates.append(entry / "frontend")
    except Exception:
        pass

    logging.info("Checking %d candidates:", len(candidates))
    for c in candidates:
        exists = (c / "package.json").exists()
        logging.info("  %s -> package.json exists=%s", c, exists)
        if exists:
            return c

    raise SystemExit(
        f"Could not find frontend directory with package.json. "
        f"cwd={cwd}. Check logs above for directory listing."
    )


def run_command(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    logging.info("Running command: %s", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=str(cwd), env=env, check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed with exit code %s: %s", exc.returncode, " ".join(cmd))
        raise


def resolve_binary(name: str) -> str:
    direct_match = shutil.which(name)
    if direct_match:
        return direct_match

    candidates = [
        os.getenv("NVM_BIN"),
        os.getenv("NODE_BIN_DIR"),
        str(Path.home() / ".nvm" / "versions" / "node"),
        "/home/cdsw/.nvm/versions/node",
    ]

    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = Path(candidate)
        if candidate_path.is_file() and candidate_path.name == name:
            return str(candidate_path)
        if candidate_path.is_dir():
            direct_bin = candidate_path / name
            if direct_bin.exists():
                return str(direct_bin)
            for nested_bin in sorted(candidate_path.glob(f"*/bin/{name}"), reverse=True):
                if nested_bin.exists():
                    return str(nested_bin)

    raise SystemExit(
        f"Could not find '{name}' in PATH. "
        "Make sure Node.js and npm are available in the CAI runtime."
    )


def dependencies_need_install(frontend_dir: Path) -> bool:
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        return True

    required_modules = [
        "next",
        "react",
        "react-dom",
        "recharts",
        "@mui/icons-material",
        "@mui/material",
        "@emotion/react",
        "@emotion/styled",
    ]
    return any(not (node_modules / module_name).exists() for module_name in required_modules)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logging.info("Starting Ask Data frontend")
    logging.info("Working directory: %s", Path.cwd())

    frontend_dir = resolve_frontend_dir()
    port = resolve_port()
    api_base_url = os.getenv("BACKEND_API_BASE_URL") or os.getenv("NEXT_PUBLIC_API_BASE_URL")

    if not api_base_url:
        raise SystemExit("BACKEND_API_BASE_URL or NEXT_PUBLIC_API_BASE_URL is not set")

    env = os.environ.copy()
    env["PORT"] = str(port)
    env["HOST"] = "127.0.0.1"
    env["HOSTNAME"] = "127.0.0.1"

    npm_bin = resolve_binary("npm")
    node_bin = resolve_binary("node")
    node_bin_dir = str(Path(node_bin).parent)
    env["PATH"] = f"{node_bin_dir}:{env.get('PATH', '')}"

    logging.info("Resolved frontend dir: %s", frontend_dir)
    logging.info("Port: %s", port)
    logging.info("Backend API base URL is configured")
    logging.info("Resolved npm: %s", npm_bin)
    logging.info("Resolved node: %s", node_bin)

    if dependencies_need_install(frontend_dir):
        run_command([npm_bin, "install", "--legacy-peer-deps"], cwd=frontend_dir, env=env)

    run_command([npm_bin, "run", "build"], cwd=frontend_dir, env=env)

    run_command(
        [node_bin, "node_modules/next/dist/bin/next", "start",
         "--hostname", "127.0.0.1", "--port", str(port)],
        cwd=frontend_dir,
        env=env,
    )


if __name__ == "__main__":
    main()
