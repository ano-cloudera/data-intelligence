from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SqlQueryRequest(BaseModel):
    sql: str = Field(..., description="SELECT SQL query against customer_aggregation table")


class RekeningRequest(BaseModel):
    cif: str | None = Field(None, description="Filter by CIF nasabah")
    jenis_rekening: str | None = Field(None, description="Filter by jenis rekening: Tabungan/Giro/Deposito")
    status_rekening: int | None = Field(None, description="Filter by status: 0=Aktif, 1=Dormant, 2=Tutup")
    limit: int = Field(default=20, ge=1, le=100)


class SaldoAnalysisRequest(BaseModel):
    jenis_rekening: str | None = Field(None, description="Filter by jenis rekening")
    status_rekening: int | None = Field(None, description="Filter by status: 0=Aktif, 1=Dormant, 2=Tutup")


class StatusRekeningRequest(BaseModel):
    jenis_rekening: str | None = Field(None, description="Filter by jenis rekening")
    cabang: str | None = Field(None, description="Filter by kode cabang")


class ToolResponse(BaseModel):
    tool: str
    result: Any
