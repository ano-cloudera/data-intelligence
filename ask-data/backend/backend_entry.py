import logging
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path


REQUIRED_PACKAGES = ["fastapi", "uvicorn", "impyla", "chromadb", "openai", "pysqlite3"]


def resolve_port() -> int:
    raw_port = os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "8080"
    try:
        return int(raw_port)
    except ValueError:
        return 8080


def resolve_backend_dir() -> Path:
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
        cwd / "data-intelligence" / "ask-data" / "backend",
        cwd / "ask-data" / "backend",
        cwd / "backend",
    ]

    # Scan one level deep under cwd
    try:
        for entry in sorted(cwd.iterdir()):
            if entry.is_dir():
                candidates.append(entry / "ask-data" / "backend")
                candidates.append(entry / "backend")
    except Exception:
        pass

    logging.info("Checking %d candidates:", len(candidates))
    for c in candidates:
        exists = (c / "app").exists()
        logging.info("  %s -> app/exists=%s", c, exists)
        if exists:
            return c

    logging.error("Could not locate backend dir. cwd=%s", cwd)
    return cwd


def _missing_packages() -> list[str]:
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            metadata.version(pkg)
            logging.info("%s: installed", pkg)
        except metadata.PackageNotFoundError:
            logging.warning("%s: NOT installed", pkg)
            missing.append(pkg)
    return missing


def run_command(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    logging.info("Running command: %s", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=str(cwd), env=env, check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed with exit code %s: %s", exc.returncode, " ".join(cmd))
        raise


def ensure_runtime_dependencies(backend_dir: Path, env: dict[str, str]) -> None:
    missing = _missing_packages()
    if not missing:
        logging.info("All required packages present.")
        return

    requirements_file = backend_dir / "requirements.txt"
    if not requirements_file.exists():
        raise SystemExit(
            f"Missing packages {missing} and requirements.txt not found at {requirements_file}."
        )

    logging.warning("Missing packages: %s — installing from requirements.txt...", missing)
    run_command(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "-q"],
        cwd=backend_dir,
        env=env,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logging.info("Starting Ask Data backend")
    logging.info("Working directory: %s", Path.cwd())

    backend_dir = resolve_backend_dir()
    port = resolve_port()

    logging.info("Resolved backend dir: %s", backend_dir)
    logging.info("Port: %s", port)

    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{backend_dir}:{pythonpath}" if pythonpath else str(backend_dir)

    ensure_runtime_dependencies(backend_dir, env)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "info",
    ]

    logging.info("Launching command: %s", " ".join(cmd))

    process = subprocess.Popen(cmd, cwd=str(backend_dir), env=env)
    process.wait()

    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
