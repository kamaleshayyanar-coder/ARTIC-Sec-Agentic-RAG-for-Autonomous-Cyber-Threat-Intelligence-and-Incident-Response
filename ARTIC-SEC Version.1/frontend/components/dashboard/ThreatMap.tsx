"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { Globe, Shield, MapPin, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { getGeoAlerts, type AlertItem } from "@/lib/api";
import { formatRiskScore } from "@/lib/utils";

// MapLibre dynamic component to protect SSR
const DynamicMap = dynamic(
  async () => {
    const { default: Map, Marker, Popup, NavigationControl } = await import("react-map-gl/maplibre");
    return function MapLibreView({ markers }: { markers: AlertItem[] }) {
      const [popupInfo, setPopupInfo] = useState<AlertItem | null>(null);

      return (
        <Map
          initialViewState={{
            longitude: 0,
            latitude: 20,
            zoom: 1.2,
          }}
          style={{ width: "100%", height: "100%" }}
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        >
          <NavigationControl position="bottom-right" />

          {markers.map((m) => {
            const lat = m.lat ?? m.latitude ?? 20;
            const lon = m.lon ?? m.longitude ?? 0;
            const isHigh = m.risk_score >= 0.7;

            return (
              <Marker
                key={m.id}
                longitude={lon}
                latitude={lat}
                anchor="center"
                onClick={(e) => {
                  e.originalEvent.stopPropagation();
                  setPopupInfo(m);
                }}
              >
                <div className="relative group cursor-pointer">
                  <span
                    className={`relative flex h-3 w-3 rounded-full ${
                      isHigh ? "bg-rose-500 shadow-[0_0_10px_#f43f5e]" : "bg-amber-400 shadow-[0_0_8px_#f59e0b]"
                    }`}
                  >
                    <span
                      className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                        isHigh ? "bg-rose-400" : "bg-amber-300"
                      }`}
                    />
                  </span>
                </div>
              </Marker>
            );
          })}

          {popupInfo && (
            <Popup
              anchor="top"
              longitude={popupInfo.lon ?? popupInfo.longitude ?? 0}
              latitude={popupInfo.lat ?? popupInfo.latitude ?? 20}
              onClose={() => setPopupInfo(null)}
              closeButton={false}
              className="z-50"
            >
              <div className="p-2 rounded bg-night-950 border border-slate-700 text-xs font-mono text-slate-200">
                <div className="font-bold text-rose-400">{popupInfo.type}</div>
                <div className="text-[11px] text-slate-300 mt-1">Source: {popupInfo.src_ip}</div>
                <div className="text-[11px] text-slate-400">Target: {popupInfo.dst_ip}</div>
                <div className="text-[11px] text-amber-400 mt-1">
                  Risk: {formatRiskScore(popupInfo.risk_score)} ({popupInfo.severity})
                </div>
              </div>
            </Popup>
          )}
        </Map>
      );
    };
  },
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center text-xs text-slate-500 font-mono">
        Loading Global Threat Telemetry Map...
      </div>
    ),
  }
);

export function ThreatMap({ height = 400 }: { height?: number }) {
  const [geoAlerts, setGeoAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    getGeoAlerts(40)
      .then((data) => {
        if (mounted) setGeoAlerts(data);
      })
      .catch((err) => console.warn("Geo alerts load error", err))
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <Card className="flex flex-col border-slate-800 bg-night-900/80 overflow-hidden">
      <CardHeader className="p-4 pb-2 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-sky-500/10 border border-sky-500/20">
            <Globe className="h-4 w-4 text-sky-400" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Global Geo-Threat Telemetry
            </CardTitle>
            <p className="text-[11px] text-slate-400">Real-time origin coordinate mappings & attack vectors</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 relative" style={{ height }}>
        <DynamicMap markers={geoAlerts} />
      </CardContent>
    </Card>
  );
}
