"use client";

import React, { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import { Share2, RefreshCw, ZoomIn, ZoomOut, Maximize2, Info } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getGraph, type GraphPayload, type GraphNode } from "@/lib/api";

// Dynamically import react-force-graph-2d to prevent SSR canvas issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-xs text-slate-500 font-mono">
      Initializing MITRE ATT&CK Force Graph...
    </div>
  ),
});

interface AttackGraphProps {
  incidentId?: number;
  height?: number;
}

export function AttackGraph({ incidentId, height = 460 }: AttackGraphProps) {
  const [data, setData] = useState<GraphPayload>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const fgRef = useRef<any>(null);

  const fetchGraphData = async () => {
    setLoading(true);
    try {
      const graphData = await getGraph(incidentId);
      setData(graphData);
    } catch (err) {
      console.warn("Graph load failed, using fallback topology", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, [incidentId]);

  const getNodeColor = (node: any) => {
    const type = (node.type || "").toLowerCase();
    switch (type) {
      case "attacker":
        return "#f43f5e"; // rose
      case "technique":
        return "#f59e0b"; // amber
      case "tactic":
        return "#38bdf8"; // sky
      case "asset":
        return "#34d399"; // emerald
      default:
        return "#94a3b8"; // slate
    }
  };

  const handleZoomIn = () => {
    if (fgRef.current) fgRef.current.zoom(fgRef.current.zoom() * 1.3, 400);
  };

  const handleZoomOut = () => {
    if (fgRef.current) fgRef.current.zoom(fgRef.current.zoom() * 0.7, 400);
  };

  const handleResetZoom = () => {
    if (fgRef.current) fgRef.current.zoomToFit(400, 30);
  };

  return (
    <Card className="relative flex flex-col border-slate-800 bg-night-900/80 overflow-hidden">
      <CardHeader className="p-4 pb-2 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-amber-500/10 border border-amber-500/20">
            <Share2 className="h-4 w-4 text-amber-400" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Attack Graph & MITRE Lineage
            </CardTitle>
            <p className="text-[11px] text-slate-400">
              Neo4j knowledge graph topology (Attacker → Technique → Asset)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomIn}
            className="h-7 w-7 text-slate-400 hover:text-white"
            title="Zoom In"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomOut}
            className="h-7 w-7 text-slate-400 hover:text-white"
            title="Zoom Out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleResetZoom}
            className="h-7 w-7 text-slate-400 hover:text-white"
            title="Reset Layout"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={fetchGraphData}
            className="h-7 w-7 text-slate-400 hover:text-white"
            title="Reload Graph"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0 relative flex-1 min-h-[400px]" style={{ height }}>
        {/* Node Category Legend */}
        <div className="absolute top-3 left-3 z-10 flex flex-wrap gap-2 rounded-lg border border-slate-800 bg-night-950/80 p-2 text-[10px] font-mono backdrop-blur-sm">
          <span className="flex items-center gap-1 text-slate-300">
            <span className="h-2 w-2 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e]" /> Attacker
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <span className="h-2 w-2 rounded-full bg-amber-500 shadow-[0_0_6px_#f59e0b]" /> Technique
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <span className="h-2 w-2 rounded-full bg-sky-400 shadow-[0_0_6px_#38bdf8]" /> Tactic
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" /> Asset
          </span>
        </div>

        {/* Selected Node Inspector Drawer */}
        {selectedNode && (
          <div className="absolute bottom-3 left-3 right-3 sm:right-auto sm:max-w-xs z-10 rounded-lg border border-slate-700 bg-night-950/95 p-3 text-xs shadow-2xl backdrop-blur-md animate-in fade-in-0 slide-in-from-bottom-2">
            <div className="flex items-center justify-between font-mono font-bold text-slate-200">
              <span className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: getNodeColor(selectedNode) }}
                />
                {selectedNode.name || selectedNode.id}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-500 hover:text-slate-300 p-0.5"
              >
                ✕
              </button>
            </div>
            <div className="mt-1 text-[11px] text-slate-400 capitalize">
              Entity Type: <span className="text-slate-300 font-mono">{selectedNode.type}</span>
            </div>
            {selectedNode.description && (
              <p className="mt-1.5 text-[11px] text-slate-300 leading-relaxed max-h-24 overflow-y-auto">
                {selectedNode.description}
              </p>
            )}
          </div>
        )}

        {typeof window !== "undefined" && (
          <ForceGraph2D
            ref={fgRef}
            graphData={data}
            nodeLabel="name"
            nodeColor={getNodeColor}
            nodeVal={(node: any) => (node.type === "technique" ? 7 : node.type === "attacker" ? 8 : 5)}
            linkColor={() => "rgba(148, 163, 184, 0.25)"}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={0.9}
            linkDirectionalParticles={1}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={2}
            linkDirectionalParticleColor={() => "#38bdf8"}
            onNodeClick={(node: any) => setSelectedNode(node)}
            backgroundColor="#05070c"
            cooldownTicks={100}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
          />
        )}
      </CardContent>
    </Card>
  );
}
