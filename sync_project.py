import os
import subprocess


def main() -> int:
    repo_dir = os.environ.get("REPO_DIR", "/home/cdsw/bank-jawa-timur")
    branch = os.environ.get("SYNC_BRANCH", "main")
    sync_mode = os.environ.get("SYNC_MODE", "safe").strip().lower()

    if sync_mode not in {"safe", "force"}:
        print(f"[ERROR] Invalid SYNC_MODE: {sync_mode}. Use 'safe' or 'force'.")
        return 1

    script_name = "sync_repo_safe.sh" if sync_mode == "safe" else "sync_repo_force.sh"
    script_path = os.environ.get(
        "SYNC_SCRIPT",
        os.path.join(repo_dir, "scripts", script_name),
    )

    print("[INFO] Sync configuration")
    print(f"[INFO] REPO_DIR   = {repo_dir}")
    print(f"[INFO] BRANCH     = {branch}")
    print(f"[INFO] SYNC_MODE  = {sync_mode}")
    print(f"[INFO] SCRIPT     = {script_path}")

    if not os.path.exists(script_path):
        print(f"[ERROR] Sync script not found: {script_path}")
        return 1

    cmd = ["bash", script_path, repo_dir, branch]
    print(f"[INFO] Running command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Sync failed with exit code {exc.returncode}")
        return exc.returncode

    print("[INFO] Sync completed successfully")
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        raise RuntimeError(f"Sync failed with exit code {exit_code}")