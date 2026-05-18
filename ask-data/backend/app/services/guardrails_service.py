from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.domain_config import get_domain_config
from app.services.chat_router import is_indonesian_text

PROMPT_INJECTION_PATTERNS = (
    r"\bignore (all |any |the )?(previous|prior|above) (instructions|rules|prompts?)\b",
    r"\bdisregard (all |any |the )?(previous|prior|above) (instructions|rules|prompts?)\b",
    r"\boverride\b.*\b(system|safety|policy|guardrail|instruction)\b",
    r"\breveal\b.*\b(system prompt|hidden prompt|developer message|instruction)\b",
    r"\bpretend to be\b.*\b(root|admin|developer)\b",
    r"\bact as\b.*\bwithout restrictions\b",
    r"\bjailbreak\b",
)

SENSITIVE_DATA_PATTERNS = (
    r"\b(account number|nomor rekening|rekening nasabah)\b",
    r"\b(phone number|mobile number|nomor telepon|nomor hp|no hp|no\. hp|handphone|whatsapp|wa nasabah)\b",
    r"\b(email address|alamat email|email nasabah)\b",
    r"\b(home address|alamat rumah|alamat lengkap|alamat nasabah)\b",
    r"\b(nik|ktp|cif|passport|ssn|tax id|npwp)\b",
    r"\b(show|list|export|dump|download)\b.*\b(all|entire|full)\b.*\b(customers|nasabah)\b",
    r"\b(tampilkan|keluarkan|lihatkan|berikan|minta|ambil|export|unduh)\b.*\b(email|alamat|telepon|hp|handphone|rekening)\b",
    r"\b(raw|detail(?:ed)?)\b.*\b(customer|nasabah)\b",
)

OUT_OF_SCOPE_PATTERNS = (
    r"\b(weather|football|movie|music|recipe|stock tip|crypto)\b",
    r"\b(cuaca|sepak bola|film|musik|resep)\b",
)

TOXIC_PATTERNS = (
    r"\b(stupid|idiot|moron|bodoh|goblok|tolol)\b",
    r"\b(shut up|diam saja)\b",
)

EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\-\s()]{7,}\d)")
LONG_ID_PATTERN = re.compile(r"(?<!\d)\d{10,}(?!\d)")
ACCOUNT_LABEL_PATTERN = re.compile(
    r"\b(account number|nomor rekening|phone number|nomor hp|nomor telepon|email address|alamat email|nik|npwp)\b",
    re.IGNORECASE,
)

SENSITIVE_COLUMN_MARKERS = {
    "account",
    "rekening",
    "email",
    "phone",
    "telepon",
    "hp",
    "mobile",
    "handphone",
    "address",
    "alamat",
    "nik",
    "npwp",
    "passport",
    "ssn",
}

AGGREGATE_CUSTOMER_ALLOW_PATTERNS = (
    r"\b(total|jumlah|count|berapa)\b.*\b(customer|customers|nasabah)\b",
    r"\b(customer|customers|nasabah)\b.*\b(per bulan|bulanan|by month|monthly|per segment|by segment|per city|by city|per region|by region)\b",
    r"\b(tren|trend)\b.*\b(customer|customers|nasabah)\b",
)

BLOCK_REASON_MESSAGES = {
    "prompt_injection": (
        "I can help with deposit, credit, and customer analytics, but I can't follow requests that bypass system rules or safety controls.",
        "Saya bisa membantu analisis deposito, kredit, dan nasabah, tetapi saya tidak bisa mengikuti permintaan yang mencoba melewati aturan sistem atau kontrol keamanan.",
    ),
    "sensitive_data": (
        "I can summarize portfolio data, but I can't expose raw personal or sensitive customer information. Try asking for aggregated results instead.",
        "Saya bisa membantu ringkasan data portofolio, tetapi saya tidak bisa menampilkan data pribadi atau sensitif nasabah secara mentah. Coba minta hasil agregat sebagai gantinya.",
    ),
    "out_of_scope": None,  # loaded dynamically from domain_config
    "toxic_language": (
        "Please rephrase the request in a professional way and I will continue to help.",
        "Silakan tuliskan ulang permintaannya dengan bahasa yang profesional, lalu saya akan bantu lanjut.",
    ),
    "sensitive_result": (
        "I can summarize the analysis, but I can't return answers based on raw sensitive customer fields. Please use aggregated or masked data instead.",
        "Saya bisa membantu ringkasan analisis, tetapi saya tidak bisa mengembalikan jawaban yang berasal dari field sensitif nasabah secara mentah. Silakan gunakan data agregat atau yang sudah dimasking.",
    ),
}


class GuardrailsServiceError(RuntimeError):
    """Raised when guardrails screening fails unexpectedly."""


@dataclass(slots=True)
class GuardrailsDecision:
    action: str
    reason: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class GuardrailsService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_runtime_status(self) -> dict[str, Any]:
        return {
            "enabled": self.settings.guardrails_enabled,
            "configured": self.settings.is_guardrails_configured,
            "mode": self.settings.guardrails_mode,
            "remote_endpoint_configured": bool(self.settings.guardrails_base_url.strip()),
            "fail_open": self.settings.guardrails_fail_open,
        }

    def screen_question(self, question: str) -> GuardrailsDecision:
        cleaned_question = question.strip()
        if not cleaned_question:
            return GuardrailsDecision(action="allow")

        heuristic_decision = self._heuristic_screen(cleaned_question)
        if heuristic_decision.action != "allow":
            return heuristic_decision

        if not self.settings.is_guardrails_configured:
            return GuardrailsDecision(action="allow")

        if not self.settings.guardrails_base_url.strip():
            return GuardrailsDecision(
                action="allow",
                metadata={"provider": "local-only", "reason": "guardrails_base_url_missing"},
            )

        try:
            remote_decision = self._remote_screen(cleaned_question)
        except Exception as exc:
            if self.settings.guardrails_fail_open:
                return GuardrailsDecision(
                    action="allow",
                    metadata={"provider": "remote-failed-open", "error": str(exc)},
                )
            raise GuardrailsServiceError(str(exc)) from exc

        return remote_decision

    def screen_result_columns(
        self,
        question: str,
        columns: list[str],
    ) -> GuardrailsDecision:
        lowered_columns = [column.lower() for column in columns]
        for column in lowered_columns:
            if any(marker in column for marker in SENSITIVE_COLUMN_MARKERS):
                return self._blocked("sensitive_result", question)

        return GuardrailsDecision(action="allow", metadata={"provider": "heuristic"})

    def protect_answer_text(self, question: str, answer: str) -> GuardrailsDecision:
        original = answer.strip()
        if not original:
            return GuardrailsDecision(action="allow", metadata={"provider": "heuristic"}, message=original)

        sanitized = EMAIL_PATTERN.sub("[redacted-email]", original)
        sanitized = LONG_ID_PATTERN.sub("[redacted-id]", sanitized)
        sanitized = PHONE_PATTERN.sub("[redacted-phone]", sanitized)

        if sanitized != original:
            return GuardrailsDecision(
                action="redact",
                reason="pii_redacted",
                message=sanitized,
                metadata={"provider": "heuristic"},
            )

        if ACCOUNT_LABEL_PATTERN.search(original):
            return self._blocked("sensitive_result", question)

        return GuardrailsDecision(
            action="allow",
            message=original,
            metadata={"provider": "heuristic"},
        )

    def _heuristic_screen(self, question: str) -> GuardrailsDecision:
        lowered = question.lower()

        if any(re.search(pattern, lowered) for pattern in AGGREGATE_CUSTOMER_ALLOW_PATTERNS):
            return GuardrailsDecision(action="allow", metadata={"provider": "heuristic-aggregate-allow"})

        if any(re.search(pattern, lowered) for pattern in PROMPT_INJECTION_PATTERNS):
            return self._blocked("prompt_injection", question)
        if any(re.search(pattern, lowered) for pattern in SENSITIVE_DATA_PATTERNS):
            return self._blocked("sensitive_data", question)
        if any(re.search(pattern, lowered) for pattern in OUT_OF_SCOPE_PATTERNS):
            return self._blocked("out_of_scope", question)
        if any(re.search(pattern, lowered) for pattern in TOXIC_PATTERNS):
            return self._blocked("toxic_language", question)

        return GuardrailsDecision(action="allow", metadata={"provider": "heuristic"})

    def _remote_screen(self, question: str) -> GuardrailsDecision:
        base_url = self.settings.guardrails_base_url.rstrip("/")
        headers = {
            "Authorization": f"Bearer {self.settings.guardrails_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"input": question, "context": {"application": "ask-data"}}

        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{base_url}/validate", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict):
            raise GuardrailsServiceError("Guardrails response was not a JSON object.")

        action = str(data.get("action", "allow")).lower()
        if action not in {"allow", "block", "redact"}:
            action = "allow"

        reason = data.get("reason")
        message = data.get("message")
        return GuardrailsDecision(
            action=action,
            reason=str(reason) if isinstance(reason, str) else None,
            message=str(message) if isinstance(message, str) else None,
            metadata={"provider": "remote", "raw": data},
        )

    def _blocked(self, reason: str, question: str) -> GuardrailsDecision:
        messages = BLOCK_REASON_MESSAGES[reason]
        if messages is None:
            dc = get_domain_config()
            english_message = dc.guardrail_out_of_scope_en
            indonesian_message = dc.guardrail_out_of_scope_id
        else:
            english_message, indonesian_message = messages
        return GuardrailsDecision(
            action="block",
            reason=reason,
            message=indonesian_message if is_indonesian_text(question) else english_message,
            metadata={"provider": "heuristic"},
        )
