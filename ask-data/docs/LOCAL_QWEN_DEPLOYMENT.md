# Local Qwen Deployment — Cloudera AI Workbench

## 1. Start Workbench session

Recommended first PoC setting:
- GPU: 1 L4 GPU
- RAM: 32 GB or higher
- Python: 3.10 or 3.11

## 2. Install dependencies

```bash
bash scripts/local_bootstrap.sh
```

## 3. Start vLLM

```bash
export QWEN_MODEL="Qwen/Qwen3-8B-AWQ"
export QWEN_MAX_MODEL_LEN=4096
export QWEN_GPU_MEMORY_UTILIZATION=0.85

bash qwen_inference/start_qwen_vllm.sh
```

## 4. Test inference

```bash
bash qwen_inference/test_qwen.sh
```

## 5. Backend env vars

```bash
LLM_PROVIDER=local_qwen
QWEN_BASE_URL=http://localhost:8000/v1
QWEN_API_KEY=local-dev-token
QWEN_MODEL=Qwen/Qwen3-8B-AWQ
```

If Qwen is deployed as separate CAI Application, use the app URL:

```bash
QWEN_BASE_URL=https://<qwen-app-url>/v1
```

## 6. Production note for ECS

For PoC, one repo is acceptable:
- frontend
- backend
- qwen inference scaffold
- sql
- data generator

For production, separate runtime ownership is cleaner:
- backend application
- frontend application
- inference service/application
- data pipeline
