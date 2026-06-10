"use client";

import { useEffect, useRef } from "react";

export interface MapFeature {
  cabang: string;
  cabang_name: string;
  kota: string;
  lat: number;
  lng: number;
  total: number;
  aktif: number;
  dormant: number;
  pct_dormant: number;
  avg_saldo: number;
}

interface ResultMapCardProps {
  features: MapFeature[];
  metric?: string;
}

function getColor(value: number, max: number): string {
  if (max === 0) return "#3b82f6";
  const ratio = value / max;
  if (ratio >= 0.8) return "#dc2626";
  if (ratio >= 0.6) return "#ea580c";
  if (ratio >= 0.4) return "#d97706";
  if (ratio >= 0.2) return "#16a34a";
  return "#3b82f6";
}

function getRadius(value: number, max: number): number {
  if (max === 0) return 8;
  return 8 + (value / max) * 22;
}

function formatSaldo(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}M`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}jt`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}rb`;
  return String(n);
}

export default function ResultMapCard({ features, metric = "total" }: ResultMapCardProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletRef = useRef<any>(null);

  useEffect(() => {
    if (!mapRef.current || features.length === 0) return;

    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      require("leaflet/dist/leaflet.css");

      if (cancelled || !mapRef.current) return;

      // Clean up previous instance
      if (leafletRef.current) {
        leafletRef.current.remove();
        leafletRef.current = null;
      }

      const map = L.map(mapRef.current, {
        center: [-7.5, 112.7],
        zoom: 8,
        scrollWheelZoom: true,
      });
      leafletRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 18,
      }).addTo(map);

      // Compute max for scaling
      const getValue = (f: MapFeature) => {
        if (metric === "dormant") return f.dormant;
        if (metric === "avg_saldo") return f.avg_saldo;
        if (metric === "pct_dormant") return f.pct_dormant;
        return f.total;
      };
      const maxVal = Math.max(...features.map(getValue), 1);

      features.forEach((f) => {
        const val = getValue(f);
        const color = getColor(val, maxVal);
        const radius = getRadius(val, maxVal);

        const circle = L.circleMarker([f.lat, f.lng], {
          radius,
          fillColor: color,
          color: "#fff",
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.75,
        }).addTo(map);

        const metricLabel =
          metric === "avg_saldo"
            ? `Avg Saldo: Rp ${formatSaldo(f.avg_saldo)}`
            : metric === "pct_dormant"
            ? `% Dormant: ${f.pct_dormant.toFixed(1)}%`
            : metric === "dormant"
            ? `Dormant: ${f.dormant.toLocaleString()}`
            : `Total: ${f.total.toLocaleString()}`;

        circle.bindPopup(
          `<div style="font-size:13px;line-height:1.6">
            <strong>${f.cabang_name}</strong><br/>
            Kota: ${f.kota}<br/>
            ${metricLabel}<br/>
            Aktif: ${f.aktif.toLocaleString()} | Dormant: ${f.dormant.toLocaleString()}<br/>
            Avg Saldo: Rp ${f.avg_saldo.toLocaleString("id-ID")}
          </div>`
        );
      });
    })();

    return () => {
      cancelled = true;
      if (leafletRef.current) {
        leafletRef.current.remove();
        leafletRef.current = null;
      }
    };
  }, [features, metric]);

  const metricLabel: Record<string, string> = {
    total: "Total Rekening",
    dormant: "Rekening Dormant",
    avg_saldo: "Rata-rata Saldo",
    pct_dormant: "% Dormant",
  };

  return (
    <div
      style={{
        background: "#1e2130",
        border: "1px solid #2d3250",
        borderRadius: 12,
        overflow: "hidden",
        marginTop: 12,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 16px",
          borderBottom: "1px solid #2d3250",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 16 }}>🗺️</span>
        <span style={{ color: "#e2e8f0", fontWeight: 600, fontSize: 14 }}>
          Peta Cabang Jawa Timur
        </span>
        <span
          style={{
            marginLeft: "auto",
            background: "#334155",
            color: "#94a3b8",
            fontSize: 11,
            padding: "2px 8px",
            borderRadius: 6,
          }}
        >
          {metricLabel[metric] ?? metric} · {features.length} cabang
        </span>
      </div>

      {/* Map container */}
      <div ref={mapRef} style={{ height: 420, width: "100%", background: "#0f172a" }} />

      {/* Legend */}
      <div
        style={{
          padding: "8px 16px",
          display: "flex",
          gap: 16,
          alignItems: "center",
          borderTop: "1px solid #2d3250",
        }}
      >
        <span style={{ color: "#64748b", fontSize: 11 }}>Skala warna:</span>
        {[
          { color: "#3b82f6", label: "Rendah" },
          { color: "#16a34a", label: "" },
          { color: "#d97706", label: "" },
          { color: "#ea580c", label: "" },
          { color: "#dc2626", label: "Tinggi" },
        ].map(({ color, label }) => (
          <span key={color} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: color,
                display: "inline-block",
              }}
            />
            {label && <span style={{ color: "#94a3b8", fontSize: 11 }}>{label}</span>}
          </span>
        ))}
        <span style={{ marginLeft: "auto", color: "#64748b", fontSize: 11 }}>
          Klik marker untuk detail
        </span>
      </div>
    </div>
  );
}
