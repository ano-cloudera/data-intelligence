# Integration Notes

## Backend replacement strategy

Existing flow:
```text
/chat/query -> build prompt -> external LLM -> SQL -> Impala -> narration -> frontend
```

Target flow:
```text
/chat/query -> build customer_dormant_segment prompt -> Qwen/vLLM -> SQL -> Impala -> Qwen narration -> frontend
```

## Code integration

1. Copy `backend/llm/qwen_client.py` into existing backend.
2. Load `backend/llm/customer_dormant_segment_sql_prompt.md` as schema prompt.
3. In the old LLM provider factory, route `LLM_PROVIDER=local_qwen` to `QwenClient`.
4. Hide Azure OpenAI and Bedrock provider picker in frontend.
5. Update starter prompts to Bahasa Indonesia.
6. Keep guardrails before SQL generation and after query result.

## Health endpoint addition

Recommended `/health` fields:

```json
{
  "status": "ok",
  "llm_provider": "local_qwen",
  "qwen_base_url": "http://localhost:8000/v1",
  "qwen_model": "Qwen/Qwen3-8B-AWQ",
  "guardrails_enabled": true,
  "session_backend": "sqlite"
}
```

## Guardrail rules

Block direct request for:
- NIK
- CIF
- nomor rekening
- nomor HP
- email
- alamat
- raw account detail

Allow:
- customer_id as analytics identifier
- aggregate segment analysis
- branch-level dormant risk
- top-N customer analytics with LIMIT 20
