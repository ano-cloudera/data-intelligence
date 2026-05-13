# Ask Data API Contract

This document summarizes the main backend endpoints used by the frontend and demo flow.

## Base behavior

- All responses are JSON.
- Runtime validation is expected to happen later inside Cloudera AI.
- `/chat/query` is the main business-demo endpoint.

## `GET /health`

Purpose:
- Check whether the backend application is reachable.

Example response:

```json
{
  "status": "ok",
  "service": "ask-data-backend",
  "environment": "development",
  "debug": false
}
```

## `GET /health/db`

Purpose:
- Check database connectivity using a lightweight validation query.

Example response:

```json
{
  "status": "ok",
  "database": "default",
  "result": 1
}
```

## `POST /sql/generate`

Purpose:
- Generate read-only SQL from a natural-language question.

Request:

```json
{
  "question": "Show total deposit balance by city",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "session_id": "optional-session-id",
  "original_question": "Show total deposit balance by city",
  "raw_generated_sql": "SELECT city, SUM(balance) AS total_balance FROM deposits GROUP BY city",
  "cleaned_generated_sql": "SELECT city, SUM(balance) AS total_balance FROM deposits GROUP BY city",
  "model": "gpt-4o-mini",
  "deployment": "your-deployment-name"
}
```

## `POST /sql/execute`

Purpose:
- Validate and execute safe read-only SQL against Impala.

Request:

```json
{
  "sql": "SELECT customer_id, full_name FROM customers LIMIT 10",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "executed_sql": "SELECT customer_id, full_name FROM customers LIMIT 10",
  "columns": ["customer_id", "full_name"],
  "rows": [
    {
      "customer_id": 1,
      "full_name": "John Doe"
    }
  ],
  "row_count": 1,
  "truncated": false,
  "limit_applied": false
}
```

## `POST /chat/query`

Purpose:
- Main end-to-end demo flow for natural language analytics.
- Generates SQL, validates it, executes it, and returns a human-readable answer plus transparent SQL/result details.

Request:

```json
{
  "question": "Who has the highest deposit balances?",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "session_id": "optional-session-id",
  "original_question": "Who has the highest deposit balances?",
  "answer": "The highest balances in this preview are concentrated among a small number of customer records.",
  "generated_sql": "SELECT customer_id, balance FROM deposits ORDER BY balance DESC LIMIT 100",
  "executed_sql": "SELECT customer_id, balance FROM deposits ORDER BY balance DESC LIMIT 100",
  "columns": ["customer_id", "balance"],
  "rows": [
    {
      "customer_id": 10,
      "balance": 250000000
    }
  ],
  "row_count": 1,
  "truncated": false,
  "limit_applied": true,
  "metadata": {
    "model": "gpt-4o-mini",
    "deployment": "your-deployment-name"
  }
}
```

## Notes

- `answer` is intended to be the primary business-facing response for the frontend.
- SQL and tabular fields remain available for transparency and debugging.
- Session continuity is handled through `session_id`.
