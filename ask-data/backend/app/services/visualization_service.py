from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from app.schemas.sql import VisualizationSpec


TEMPORAL_COLUMN_MARKERS = ("date", "month", "year", "week", "day", "period", "time")
PIE_COLUMN_MARKERS = ("segment", "collectibility", "category", "product", "status", "composition")
MAX_PLOT_POINTS = 8
MAX_TABLE_ROWS = 6


def _is_numeric(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if isinstance(value, str):
        try:
            float(value.replace(",", ""))
            return True
        except ValueError:
            return False
    return False


def _to_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def _to_label(value: Any) -> str:
    if value is None:
        return "Unknown"
    text = str(value).strip()
    return text or "Unknown"


def _try_parse_temporal(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    text = _to_label(value)
    patterns = (
        "%Y-%m-%d",
        "%Y-%m",
        "%Y/%m/%d",
        "%Y/%m",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y%m%d",
        "%b %Y",
        "%B %Y",
    )
    for pattern in patterns:
        try:
            parsed = datetime.strptime(text, pattern)
            if pattern == "%Y-%m":
                return parsed.replace(day=1)
            if pattern == "%Y/%m":
                return parsed.replace(day=1)
            return parsed
        except ValueError:
            continue

    iso_match = re.fullmatch(r"(\d{4})-Q([1-4])", text)
    if iso_match:
        year = int(iso_match.group(1))
        quarter = int(iso_match.group(2))
        return datetime(year, ((quarter - 1) * 3) + 1, 1)

    return None


def _looks_temporal(name: str, sample: Any) -> bool:
    lowered = name.lower()
    if any(marker in lowered for marker in TEMPORAL_COLUMN_MARKERS):
        return True
    return _try_parse_temporal(sample) is not None


def _sample_evenly(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(items) <= limit:
        return items

    step = (len(items) - 1) / (limit - 1)
    sampled_indices: list[int] = []
    for index in range(limit):
        candidate = round(index * step)
        if sampled_indices and candidate <= sampled_indices[-1]:
            candidate = min(len(items) - 1, sampled_indices[-1] + 1)
        sampled_indices.append(candidate)

    return [items[index] for index in sampled_indices]


def _build_insight(chart_type: str, x_key: str, y_key: str, plotted_points: int, total_points: int) -> str:
    readable_x = x_key.replace("_", " ")
    readable_y = y_key.replace("_", " ")
    if chart_type == "line" and total_points > plotted_points:
        return (
            f"Trend ordered by {readable_x} using {plotted_points} representative points "
            f"from {total_points} records of {readable_y}."
        )
    if chart_type == "line":
        return f"Trend ordered by {readable_x} across {plotted_points} plotted points."
    if chart_type == "bar":
        return f"Top comparison of {readable_y} grouped by {readable_x}."
    if chart_type == "pie":
        return f"Composition share of {readable_y} grouped by {readable_x}."
    return f"Summary table of {readable_y} by {readable_x}."


class VisualizationService:
    def build_visualization(
        self,
        question: str,
        columns: list[str],
        rows: list[dict[str, Any]],
        preferred_type: str | None = None,
    ) -> VisualizationSpec | None:
        if len(columns) < 2 or len(rows) < 2:
            return None

        x_key = columns[0]
        numeric_columns = [column for column in columns[1:] if any(_is_numeric(row.get(column)) for row in rows)]
        if not numeric_columns:
            return None

        y_key = numeric_columns[0]
        filtered_rows = []
        for row in rows:
            numeric_value = _to_number(row.get(y_key))
            if numeric_value is None:
                continue
            filtered_rows.append(
                {
                    x_key: _to_label(row.get(x_key)),
                    y_key: numeric_value,
                }
            )

        if len(filtered_rows) < 2:
            return None

        sample_label = filtered_rows[0][x_key]
        is_temporal = _looks_temporal(x_key, sample_label)
        chart_type = "line" if is_temporal else "bar"
        lowered_question = question.lower()
        lowered_x = x_key.lower()

        if is_temporal:
            temporal_rows = [
                {**row, "__sort_key": _try_parse_temporal(row[x_key])}
                for row in filtered_rows
            ]
            temporal_rows = [row for row in temporal_rows if row["__sort_key"] is not None]
            if len(temporal_rows) >= 2:
                temporal_rows.sort(key=lambda item: item["__sort_key"])
                ordered_rows = [{x_key: row[x_key], y_key: row[y_key]} for row in temporal_rows]
                series = _sample_evenly(ordered_rows, MAX_PLOT_POINTS)
                table_rows = ordered_rows[-MAX_TABLE_ROWS:]
            else:
                series = _sample_evenly(filtered_rows, MAX_PLOT_POINTS)
                table_rows = filtered_rows[:MAX_TABLE_ROWS]
                chart_type = "table"
        else:
            sorted_rows = sorted(filtered_rows, key=lambda item: item[y_key], reverse=True)
            series = sorted_rows[:MAX_PLOT_POINTS]
            table_rows = series[:MAX_TABLE_ROWS]
            if len(series) <= 5 and any(marker in lowered_question or marker in lowered_x for marker in PIE_COLUMN_MARKERS):
                chart_type = "pie"

        if len(series) < 2 and chart_type != "table":
            chart_type = "table"

        if preferred_type in {"bar", "line", "pie", "table"}:
            if preferred_type == "pie" and len(series) > 5:
                chart_type = "bar"
            elif preferred_type == "line" and len(series) >= 2:
                chart_type = "line"
            elif preferred_type == "bar" and len(series) >= 2:
                chart_type = "bar"
            elif preferred_type == "table":
                chart_type = "table"
            elif preferred_type == "pie" and len(series) >= 2:
                chart_type = "pie"

        return VisualizationSpec(
            type=chart_type,
            title=f"{x_key.replace('_', ' ').title()} by {y_key.replace('_', ' ').title()}",
            x_key=x_key,
            y_key=y_key,
            series=series,
            table_columns=[x_key, y_key],
            table_rows=table_rows,
            insight=_build_insight(chart_type, x_key, y_key, len(series), len(filtered_rows)),
        )
