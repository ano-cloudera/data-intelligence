"""
CAI (Cloudera AI) REST API client.

Handles:
  - Upload file ke CAI project filesystem via API v2
  - Trigger CAI Job run dengan env var override
  - Poll status Job run

Required env vars (auto-inject di dalam CAI Application):
  CDSW_API_URL      Base URL CAI, mis. https://ml-xxx.cloudera.site
  CDSW_APIV2_KEY    API key v2 (auto-available di CAI runtime)
  CDSW_PROJECT_ID   Project ID (dari .env atau auto-inject)
  CAI_INGEST_JOB_ID Job ID untuk ingest PDF (diisi manual setelah Job dibuat di CAI)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


import httpx


class CAIClientError(RuntimeError):
    pass


class CAIClient:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        project_id: str,
    ) -> None:
        self.base = api_url.rstrip("/")
        self.project_id = project_id
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

    # ── Files ─────────────────────────────────────────────────────────────────

    def upload_file(self, local_path: str, remote_path: str) -> dict[str, Any]:
        """Upload file ke CAI project files via multipart/form-data.

        remote_path: path relatif di dalam project, mis. 'rag_uploads/doc.pdf'
        """
        url = f"{self.base}/api/v2/projects/{self.project_id}/files/{remote_path}"
        # CAI Files API butuh multipart/form-data, bukan octet-stream
        auth_headers = {"Authorization": self._headers["Authorization"]}
        with open(local_path, "rb") as f:
            try:
                resp = httpx.put(
                    url,
                    headers=auth_headers,
                    files={"file": (Path(local_path).name, f, "application/octet-stream")},
                    timeout=120.0,
                )
            except httpx.RequestError as exc:
                raise CAIClientError(f"Upload request failed: {exc}") from exc

        if resp.status_code not in (200, 201):
            raise CAIClientError(
                f"Upload failed [{resp.status_code}]: {resp.text[:300]}"
            )
        return resp.json() if resp.text else {"status": "uploaded"}

    # ── Jobs ──────────────────────────────────────────────────────────────────

    def create_job_run(
        self,
        job_id: str,
        environment: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Trigger CAI Job run dengan optional env var overrides."""
        url = f"{self.base}/api/v2/projects/{self.project_id}/jobs/{job_id}/runs"
        body: dict[str, Any] = {}
        if environment:
            body["environment"] = environment

        try:
            resp = httpx.post(
                url,
                headers={**self._headers, "Content-Type": "application/json"},
                json=body,
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            raise CAIClientError(f"Job run request failed: {exc}") from exc

        if resp.status_code not in (200, 201):
            raise CAIClientError(
                f"Create job run failed [{resp.status_code}]: {resp.text[:300]}"
            )
        return resp.json()

    def get_job_run(self, job_id: str, run_id: str) -> dict[str, Any]:
        """Get status dari Job run tertentu."""
        url = f"{self.base}/api/v2/projects/{self.project_id}/jobs/{job_id}/runs/{run_id}"
        try:
            resp = httpx.get(url, headers=self._headers, timeout=15.0)
        except httpx.RequestError as exc:
            raise CAIClientError(f"Get job run failed: {exc}") from exc

        if resp.status_code != 200:
            raise CAIClientError(
                f"Get job run failed [{resp.status_code}]: {resp.text[:300]}"
            )
        return resp.json()

    def get_job_run_status(self, job_id: str, run_id: str) -> str:
        """Return status string: ENGINE_SCHEDULING | ENGINE_RUNNING | ENGINE_SUCCEEDED | ENGINE_FAILED."""
        data = self.get_job_run(job_id, run_id)
        return data.get("status", "UNKNOWN")


def get_cai_client() -> CAIClient | None:
    """Build CAIClient dari env vars. Return None jika tidak dikonfigurasi."""
    api_url = os.getenv("CDSW_API_URL", "").strip()
    api_key = os.getenv("CDSW_APIV2_KEY", "").strip()
    project_id = os.getenv("PROJECT_ID", "").strip()

    if not all([api_url, api_key, project_id]):
        return None
    return CAIClient(api_url=api_url, api_key=api_key, project_id=project_id)
