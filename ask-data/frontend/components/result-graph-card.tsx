"use client";

import { useEffect, useRef, useState, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  label: string;
  segment: string;
  churn_risk: number;
  churn_risk_label: string;
  dormant_risk_level: string;
  credit_score: number;
  credit_risk_label: string;
  sw_amount: number;
  city: string;
  branch_name: string;
  is_root: boolean;
  risk_level: "critical" | "high" | "medium" | "low";
  contagion_score: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship_type: string;
  risk_weight: number;
}

export interface GraphData {
  root_customer_id: string;
  hop_depth: number;
  node_count: number;
  edge_count: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ── Constants ─────────────────────────────────────────────────────────────────

const SEGMENT_COLOR: Record<string, string> = {
  "Silent Mature":             "#f59e0b",
  "Young Syariah Digital":     "#10b981",
  "Konvensional Produktif":    "#6366f1",
};
const DEFAULT_SEGMENT_COLOR = "#8b5cf6";

const RISK_BORDER: Record<string, string> = {
  critical: "#dc2626",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
};

const REL_COLOR: Record<string, string> = {
  co_borrower:   "#ef4444",
  guarantor:     "#f97316",
  same_employer: "#8b5cf6",
  same_branch:   "#64748b",
};

const REL_LABEL: Record<string, string> = {
  co_borrower:   "Co-borrower",
  guarantor:     "Guarantor",
  same_employer: "Same Employer",
  same_branch:   "Same Branch",
};

const NODE_R = 22;
const W = 800;
const H = 520;

// ── Force simulation (pure JS, no D3) ────────────────────────────────────────

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  nodeNumber: number;
}

function initPositions(nodes: GraphNode[], rootId: string): SimNode[] {
  let counter = 0;
  return nodes.map((n, i) => {
    const nodeNumber = n.id === rootId ? 0 : ++counter;
    if (n.id === rootId) return { ...n, x: W / 2, y: H / 2, vx: 0, vy: 0, nodeNumber };
    const angle = (2 * Math.PI * i) / nodes.length;
    const r = 160 + Math.random() * 60;
    return { ...n, x: W / 2 + r * Math.cos(angle), y: H / 2 + r * Math.sin(angle), vx: 0, vy: 0, nodeNumber };
  });
}

function runSimulation(nodes: SimNode[], edges: GraphEdge[], steps = 120): SimNode[] {
  const byId = new Map(nodes.map((n) => [n.id, n]));

  for (let step = 0; step < steps; step++) {
    const alpha = 1 - step / steps;

    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (4000 / (dist * dist)) * alpha;
        a.vx -= (dx / dist) * force;
        a.vy -= (dy / dist) * force;
        b.vx += (dx / dist) * force;
        b.vy += (dy / dist) * force;
      }
    }

    // Attraction (edges)
    for (const e of edges) {
      const a = byId.get(e.source), b = byId.get(e.target);
      if (!a || !b) continue;
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const ideal = 140;
      const force = ((dist - ideal) / dist) * 0.08 * alpha;
      a.vx += dx * force; a.vy += dy * force;
      b.vx -= dx * force; b.vy -= dy * force;
    }

    // Root gravity
    const root = byId.get(nodes[0]?.id === nodes[0]?.id ? nodes.find(n => n.is_root)?.id ?? "" : "");
    if (root) {
      root.vx += (W / 2 - root.x) * 0.04 * alpha;
      root.vy += (H / 2 - root.y) * 0.04 * alpha;
    }

    // Apply velocity + clamp
    for (const n of nodes) {
      n.vx *= 0.85; n.vy *= 0.85;
      n.x = Math.max(NODE_R + 4, Math.min(W - NODE_R - 4, n.x + n.vx));
      n.y = Math.max(NODE_R + 4, Math.min(H - NODE_R - 4, n.y + n.vy));
    }
  }

  return nodes;
}

// ── Tooltip ───────────────────────────────────────────────────────────────────

function Tooltip({ node, x, y }: { node: GraphNode; x: number; y: number }) {
  return (
    <div
      className="pointer-events-none absolute z-50 rounded-xl border border-white/10 bg-[#0f172a]/95 px-4 py-3 shadow-2xl backdrop-blur-md"
      style={{ left: x + 16, top: y - 8, minWidth: 220 }}
    >
      <p className="mb-1 text-xs font-bold text-white">{node.id}</p>
      <p className="mb-2 text-[10px] text-slate-400">{node.segment}</p>
      <div className="space-y-1">
        {[
          ["Churn Risk",    `${node.churn_risk_label} (${(node.churn_risk * 100).toFixed(0)}%)`],
          ["Credit",        `${node.credit_risk_label} (${node.credit_score})`],
          ["Contagion",     `${(node.contagion_score * 100).toFixed(0)}%`],
          ["Balance",       `Rp ${node.sw_amount.toLocaleString("id-ID")}`],
          ["Location",      `${node.city} · ${node.branch_name}`],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between gap-4">
            <span className="text-[10px] text-slate-400">{k}</span>
            <span className="text-[10px] font-medium text-white">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Legend ────────────────────────────────────────────────────────────────────

function Legend() {
  return (
    <div className="flex flex-col gap-2 px-1 pt-3">
      <p className="text-[11px] leading-4 text-slate-300">
        Angka di dalam lingkaran = <span className="font-semibold text-white">persentase risiko churn</span> nasabah tersebut.
      </p>
      <div className="flex flex-wrap gap-x-5 gap-y-2.5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">Segmen</span>
          {Object.entries(SEGMENT_COLOR).map(([k, c]) => (
            <span key={k} className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 shrink-0 rounded-full ring-1 ring-white/20" style={{ background: c }} />
              <span className="text-[11px] font-medium text-white">{k}</span>
            </span>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">Relasi</span>
          {Object.entries(REL_COLOR).map(([k, c]) => (
            <span key={k} className="flex items-center gap-1.5">
              <span className="inline-block h-1 w-5 shrink-0 rounded-full" style={{ background: c }} />
              <span className="text-[11px] font-medium text-white">{REL_LABEL[k]}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function ResultGraphCard({ data }: { data: GraphData }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [simNodes, setSimNodes] = useState<SimNode[]>([]);
  const [hovered, setHovered] = useState<{ node: GraphNode; x: number; y: number } | null>(null);
  const [selected, setSelected] = useState<SimNode | null>(null);

  useEffect(() => {
    if (!data?.nodes?.length) return;
    const initial = initPositions(data.nodes, data.root_customer_id);
    const settled = runSimulation(initial, data.edges);
    setSimNodes([...settled]);
  }, [data]);

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGCircleElement>, node: SimNode) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHovered({ node, x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  const nodeById = new Map(simNodes.map((n) => [n.id, n]));

  // Direct relationship label to the root, for nodes one hop away.
  const directRelationToRoot = new Map<string, string>();
  for (const e of data.edges) {
    if (e.source === data.root_customer_id) directRelationToRoot.set(e.target, e.relationship_type);
    if (e.target === data.root_customer_id) directRelationToRoot.set(e.source, e.relationship_type);
  }

  function nodeSubLabel(n: SimNode): string {
    if (n.is_root) return "Root";
    const relation = directRelationToRoot.get(n.id);
    if (relation) return `${n.city} · ${REL_LABEL[relation] ?? relation}`;
    return n.city || `Nasabah ${n.nodeNumber}`;
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full max-w-[56rem] overflow-hidden rounded-2xl border border-white/8 bg-[#0b1221]"
      style={{ boxShadow: "0 0 40px rgba(99,102,241,0.08)" }}
    >
      {/* Header */}
      <div className="border-b border-white/8 px-5 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-rose-500/20 text-sm">⚠️</span>
            <span className="text-sm font-semibold text-white">Jaringan Risiko Nasabah</span>
          </div>
          <span className="text-[10px] text-slate-500">Nasabah Utama · {(data.node_count - 1)} koneksi ditemukan</span>
        </div>
        <p className="mt-2 text-[12px] leading-5 text-slate-300">
          Nasabah utama terhubung ke <span className="font-semibold text-white">{data.node_count - 1} nasabah lain</span> lewat{" "}
          {Object.entries(
            data.edges.reduce<Record<string, number>>((acc, e) => {
              acc[e.relationship_type] = (acc[e.relationship_type] ?? 0) + 1;
              return acc;
            }, {}),
          )
            .map(([type, count]) => `${count} ${REL_LABEL[type] ?? type}`)
            .join(", ")}. Jika nasabah ini gagal bayar, risiko berpotensi menyebar ke seluruh jaringan ini.
        </p>
      </div>

      {/* Graph SVG */}
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="block">
        <defs>
          {/* Glow filter for root node */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          {/* Arrow markers per relation type */}
          {Object.entries(REL_COLOR).map(([type, color]) => (
            <marker
              key={type}
              id={`arrow-${type}`}
              markerWidth="6" markerHeight="6"
              refX="5" refY="3"
              orient="auto"
            >
              <path d="M0,0 L0,6 L6,3 z" fill={color} opacity={0.7} />
            </marker>
          ))}
        </defs>

        {/* Edges */}
        {data.edges.map((e, i) => {
          const a = nodeById.get(e.source);
          const b = nodeById.get(e.target);
          if (!a || !b) return null;
          const color = REL_COLOR[e.relationship_type] ?? "#64748b";
          const opacity = 0.25 + e.risk_weight * 0.55;
          const strokeW = 1 + e.risk_weight * 2.5;
          return (
            <line
              key={i}
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={color}
              strokeWidth={strokeW}
              strokeOpacity={opacity}
              markerEnd={`url(#arrow-${e.relationship_type})`}
            />
          );
        })}

        {/* Nodes */}
        {simNodes.map((n) => {
          const fill   = SEGMENT_COLOR[n.segment] ?? DEFAULT_SEGMENT_COLOR;
          const border = RISK_BORDER[n.risk_level] ?? "#22c55e";
          const isRoot = n.is_root;
          const isSelected = selected?.id === n.id;
          const r = isRoot ? NODE_R + 6 : NODE_R;

          return (
            <g key={n.id} style={{ cursor: "pointer" }}>
              {/* Pulse ring for high-risk nodes */}
              {(n.risk_level === "critical" || n.risk_level === "high") && (
                <circle cx={n.x} cy={n.y} r={r + 6} fill="none" stroke={border} strokeWidth={1} opacity={0.3} />
              )}
              {/* Main circle */}
              <circle
                cx={n.x} cy={n.y} r={r}
                fill={fill}
                fillOpacity={isSelected ? 1 : 0.85}
                stroke={isRoot ? "#ffffff" : border}
                strokeWidth={isRoot ? 3 : isSelected ? 2.5 : 1.5}
                filter={isRoot ? "url(#glow)" : undefined}
                onMouseMove={(e) => handleMouseMove(e, n)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => setSelected(selected?.id === n.id ? null : n)}
              />
              {/* Root star label */}
              {isRoot && (
                <text x={n.x} y={n.y - r - 8} textAnchor="middle" fontSize={9} fill="#fff" fontWeight="700">
                  ★ NASABAH UTAMA
                </text>
              )}
              {/* Churn % inside node */}
              <text x={n.x} y={n.y - 2} textAnchor="middle" fontSize={11} fill="#fff" fontWeight="700" pointerEvents="none">
                {Math.round(n.churn_risk * 100)}%
              </text>
              <text x={n.x} y={n.y + 9} textAnchor="middle" fontSize={6.5} fill="rgba(255,255,255,0.75)" fontWeight="600" pointerEvents="none">
                CHURN
              </text>
              {/* Readable sub-label: city + relation to root (not the raw scrambled cif) */}
              <text x={n.x} y={n.y + r + 13} textAnchor="middle" fontSize={8} fill="#cbd5e1" pointerEvents="none">
                {nodeSubLabel(n)}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Tooltip */}
      {hovered && <Tooltip node={hovered.node} x={hovered.x} y={hovered.y} />}

      {/* Selected node detail panel */}
      {selected && (
        <div className="border-t border-white/8 bg-white/3 px-5 py-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-semibold text-white">
                {selected.is_root ? "Nasabah Utama" : `Nasabah ${selected.nodeNumber}`}
              </p>
              <p className="text-[10px] text-slate-400">{selected.segment} · {selected.city} · {selected.branch_name}</p>
            </div>
            <button onClick={() => setSelected(null)} className="text-slate-500 hover:text-white text-xs">✕</button>
          </div>
          <div className="mt-2 grid grid-cols-4 gap-3">
            {[
              { label: "Churn Risk",   value: selected.churn_risk_label,                     color: RISK_BORDER[selected.risk_level] ?? "#22c55e" },
              { label: "Credit",       value: selected.credit_risk_label,                     color: "#eab308" },
              { label: "Contagion",    value: `${(selected.contagion_score * 100).toFixed(0)}%`, color: "#f97316" },
              { label: "Balance",      value: `Rp ${(selected.sw_amount / 1_000_000).toFixed(1)}Jt`, color: "#6366f1" },
            ].map(({ label, value, color }) => (
              <div key={label} className="rounded-lg bg-white/5 px-3 py-2">
                <p className="text-[9px] uppercase tracking-widest text-slate-400">{label}</p>
                <p className="mt-0.5 text-sm font-bold" style={{ color }}>{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="border-t border-white/8 bg-black/25 px-5 pb-4 pt-1">
        <Legend />
      </div>
    </div>
  );
}
