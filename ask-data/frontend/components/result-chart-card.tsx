"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DataTable, TableCard, TableCell, TableHeadCell } from "@/components/ui/table";
import type { VisualizationSpec } from "@/lib/api";

type DataPoint = {
  label: string;
  value: number;
};

interface ResultChartCardProps {
  visualization: VisualizationSpec;
}

function formatValue(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);
}

function formatCompactValue(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    compactDisplay: "short",
    maximumFractionDigits: Math.abs(value) >= 1_000 ? 1 : 2,
  }).format(value);
}

function formatAxisLabel(label: string): string {
  const isoDate = /^\d{4}-\d{2}-\d{2}$/;
  const isoMonth = /^\d{4}-\d{2}$/;

  if (isoDate.test(label)) {
    const date = new Date(`${label}T00:00:00`);
    if (!Number.isNaN(date.getTime())) {
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
      }).format(date);
    }
  }

  if (isoMonth.test(label)) {
    const date = new Date(`${label}-01T00:00:00`);
    if (!Number.isNaN(date.getTime())) {
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        year: "numeric",
      }).format(date);
    }
  }

  return label;
}

function isNumericLike(value: unknown): boolean {
  return typeof value === "number" || (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value)));
}

function buildXAxisTicks(points: DataPoint[]): DataPoint[] {
  if (points.length <= 4) return points;
  const indices = new Set([
    0,
    Math.floor((points.length - 1) / 3),
    Math.floor(((points.length - 1) * 2) / 3),
    points.length - 1,
  ]);
  return points.filter((_, index) => indices.has(index));
}

function buildYAxisTicks(min: number, max: number): number[] {
  if (max === min) return [max, min];
  return [max, min + (max - min) / 2, min];
}

const pieColors = ["#5c63f2", "#ff7a2f", "#16a34a", "#0ea5e9", "#f59e0b", "#db2777"];

function renderViewToggle(
  activeView: "chart" | "table",
  onChange: (view: "chart" | "table") => void,
  showChart: boolean,
  showTable: boolean,
) {
  if (!showChart || !showTable) return null;

  return (
    <div className="inline-flex rounded-full border border-[var(--color-border-soft)] bg-white p-1 shadow-sm">
      {(["chart", "table"] as const).map((view) => (
        <button
          key={view}
          type="button"
          onClick={() => onChange(view)}
          className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition ${
            activeView === view
              ? "bg-[rgba(92,99,242,0.12)] text-[#4953d3]"
              : "text-[var(--color-ink-subtle)] hover:text-[var(--color-ink-strong)]"
          }`}
        >
          {view}
        </button>
      ))}
    </div>
  );
}

function renderTableView(columns: string[], rows: Array<Record<string, unknown>>) {
  if (columns.length === 0 || rows.length === 0) return null;

  return (
    <TableCard className="overflow-x-auto bg-white/80">
      <DataTable>
        <thead>
          <tr>
            {columns.map((column) => (
              <TableHeadCell key={column}>{column.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())}</TableHeadCell>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${index}-${columns.map((column) => String(row[column] ?? "")).join("-")}`} className="border-t border-[var(--color-border-soft)]">
              {columns.map((column) => {
                const cellValue = row[column];
                const numeric = isNumericLike(cellValue);
                return (
                  <TableCell key={column} numeric={numeric}>
                    {typeof cellValue === "number" ? formatValue(cellValue) : String(cellValue ?? "-")}
                  </TableCell>
                );
              })}
            </tr>
          ))}
        </tbody>
      </DataTable>
    </TableCard>
  );
}

export function ResultChartCard({ visualization }: ResultChartCardProps) {
  const kind = visualization.type;
  const xKey = visualization.x_key;
  const yKey = visualization.y_key;
  const [view, setView] = useState<"chart" | "table">(kind === "table" ? "table" : "chart");

  const points: DataPoint[] = useMemo(() => {
    if (!xKey || !yKey) return [];
    return visualization.series
      .map((item) => {
        const rawValue = item[yKey];
        const value = typeof rawValue === "number" ? rawValue : Number(rawValue);
        if (!Number.isFinite(value)) return null;
        return {
          label: String(item[xKey] ?? "Unknown"),
          value,
        };
      })
      .filter((point): point is DataPoint => point !== null);
  }, [visualization.series, xKey, yKey]);

  const boundedPoints = points.slice(0, 8);
  const showChart = kind !== "table" && boundedPoints.length >= 2;
  const tableColumns = visualization.table_columns ?? [];
  const tableRows = visualization.table_rows ?? [];
  const showTable = tableColumns.length > 0 && tableRows.length > 0;

  if (!showChart && !showTable) return null;

  const firstPoint = boundedPoints[0];
  const lastPoint = boundedPoints[boundedPoints.length - 1];
  const delta = firstPoint && lastPoint ? lastPoint.value - firstPoint.value : 0;
  const trendDirection = delta > 0 ? "Upward trend" : delta < 0 ? "Soft decline" : "Stable trend";
  const xAxisTicks = buildXAxisTicks(boundedPoints);
  const max = boundedPoints.length > 0 ? Math.max(...boundedPoints.map((point) => point.value), 1) : 1;
  const min = boundedPoints.length > 0 ? Math.min(...boundedPoints.map((point) => point.value)) : 0;
  const total = boundedPoints.reduce((sum, point) => sum + point.value, 0);
  const activeView = kind === "table" ? "table" : view;

  return (
    <section className="w-full max-w-[56rem] rounded-[var(--radius-panel)] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#ffffff_0%,#f7f9ff_100%)] p-5 shadow-panel">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
            Visual Insight
          </p>
          <h3 className="mt-1 font-headline text-lg font-bold text-[var(--color-ink-strong)]">
            {visualization.title ?? "Auto-generated chart from the latest SQL result"}
          </h3>
          {visualization.insight ? (
            <p className="mt-2 max-w-2xl text-xs leading-5 text-[var(--color-ink-muted)] sm:text-sm">{visualization.insight}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-row items-center gap-2 sm:flex-col sm:items-end">
          <span className="rounded-full bg-[rgba(92,99,242,0.1)] px-3 py-1 text-xs font-semibold text-[#4953d3]">
            {kind === "line" ? "Trend view" : kind === "pie" ? "Composition view" : kind === "table" ? "Table view" : "Comparison view"}
          </span>
          {renderViewToggle(activeView, setView, showChart, showTable)}
        </div>
      </div>

      {activeView === "table" ? renderTableView(tableColumns, tableRows) : null}

      {activeView === "chart" && kind === "bar" ? (
        <div className="h-72 rounded-[18px] border border-[var(--color-border-soft)] bg-white/80 px-3 py-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={boundedPoints} margin={{ top: 8, right: 18, bottom: 8, left: 12 }}>
              <CartesianGrid stroke="#e3e8f4" strokeDasharray="4 4" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: "#747887", fontSize: 11, fontWeight: 600 }}
                tickFormatter={formatAxisLabel}
                tickLine={false}
                axisLine={{ stroke: "#dfe5f3" }}
                interval={0}
              />
              <YAxis
                tick={{ fill: "#747887", fontSize: 11, fontWeight: 600 }}
                tickFormatter={formatCompactValue}
                tickLine={false}
                axisLine={false}
                width={64}
              />
              <Tooltip
                cursor={{ fill: "rgba(92,99,242,0.08)" }}
                formatter={(value) => [formatCompactValue(Number(value)), yKey ?? "Value"]}
                labelFormatter={(label) => formatAxisLabel(String(label))}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#5c63f2" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      {activeView === "chart" && kind === "line" ? (
        <div className="rounded-[18px] border border-[var(--color-border-soft)] bg-white/80 p-4">
          <div className="mb-4 flex flex-wrap gap-2">
            <span className="rounded-full bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-ink-muted)]">
              Latest {lastPoint ? formatCompactValue(lastPoint.value) : "-"}
            </span>
            <span className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
              delta >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
            }`}>
              {delta >= 0 ? "+" : ""}{formatCompactValue(delta)} vs start
            </span>
            <span className="rounded-full bg-[rgba(92,99,242,0.08)] px-3 py-1.5 text-xs font-semibold text-[#4953d3]">
              {trendDirection}
            </span>
          </div>

          <div className="h-64 rounded-[16px] border border-[var(--color-border-soft)] bg-[linear-gradient(180deg,#fcfdff_0%,#f7f9ff_100%)] px-2 py-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={boundedPoints} margin={{ top: 12, right: 24, bottom: 10, left: 8 }}>
                <CartesianGrid stroke="#e3e8f4" strokeDasharray="4 4" vertical={false} />
                <XAxis
                  dataKey="label"
                  tick={{ fill: "#747887", fontSize: 11, fontWeight: 600 }}
                  tickFormatter={formatAxisLabel}
                  tickLine={false}
                  axisLine={{ stroke: "#dfe5f3" }}
                  interval="preserveStartEnd"
                  minTickGap={22}
                />
                <YAxis
                  domain={["dataMin", "dataMax"]}
                  tick={{ fill: "#747887", fontSize: 11, fontWeight: 600 }}
                  tickFormatter={formatCompactValue}
                  tickLine={false}
                  axisLine={false}
                  width={72}
                />
                <Tooltip
                  formatter={(value) => [formatCompactValue(Number(value)), yKey ?? "Value"]}
                  labelFormatter={(label) => formatAxisLabel(String(label))}
                  contentStyle={{
                    border: "1px solid #dfe5f3",
                    borderRadius: "14px",
                    boxShadow: "0 18px 40px rgba(15,23,42,0.12)",
                    fontSize: "12px",
                  }}
                />
                <Line
                  type="linear"
                  dataKey="value"
                  stroke="#5c63f2"
                  strokeWidth={2.5}
                  dot={{ r: 2.5, strokeWidth: 1.5, fill: "#ffffff", stroke: "#5c63f2" }}
                  activeDot={{ r: 4, strokeWidth: 2, fill: "#ffffff", stroke: "#ff7a2f" }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {xAxisTicks.map((point) => (
              <span key={point.label} className="rounded-full bg-[var(--color-surface-muted)] px-3 py-1 text-xs font-semibold text-[var(--color-ink-subtle)]">
                {formatAxisLabel(point.label)} · {formatCompactValue(point.value)}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {activeView === "chart" && kind === "pie" ? (
        <div className="grid gap-4 rounded-[18px] border border-[var(--color-border-soft)] bg-white/80 p-4 lg:grid-cols-[18rem_minmax(0,1fr)]">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={boundedPoints} dataKey="value" nameKey="label" innerRadius={58} outerRadius={92} paddingAngle={2}>
                  {boundedPoints.map((point, index) => (
                    <Cell key={point.label} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [formatCompactValue(Number(value)), yKey ?? "Value"]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-3">
            {boundedPoints.map((point, index) => {
              const percent = total > 0 ? (point.value / total) * 100 : 0;
              return (
                <div key={point.label} className="flex items-center justify-between gap-3 rounded-[14px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-3 py-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: pieColors[index % pieColors.length] }} />
                    <p className="truncate text-sm font-semibold text-[var(--color-ink-strong)]">{point.label}</p>
                  </div>
                  <span className="shrink-0 text-sm font-semibold text-[#4953d3]">{percent.toFixed(1)}%</span>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {activeView === "chart" ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-[var(--color-ink-subtle)]">
          <span className="rounded-full bg-[var(--color-surface-muted)] px-3 py-1">
            {boundedPoints.length} plotted points
          </span>
          <span className="rounded-full bg-[var(--color-surface-muted)] px-3 py-1">
            Range {formatCompactValue(min)} to {formatCompactValue(max)}
          </span>
        </div>
      ) : null}
    </section>
  );
}
