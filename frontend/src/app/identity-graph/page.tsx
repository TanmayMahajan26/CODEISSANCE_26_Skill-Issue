"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useEffect, useRef, useState, useCallback } from "react";
import { Network, Maximize2 } from "lucide-react";
import ForceGraph2D from "@/components/ui/ForceGraph2D";

const SYSTEM_COLORS: Record<string, string> = {
  CORE_BANKING: "#3B82F6",
  CRM: "#10B981",
  LOAN_ORIGINATION: "#F59E0B",
  INSURANCE: "#EF4444",
  WEALTH: "#8B5CF6",
};

export default function IdentityGraphPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>();
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const { data: goldenRecords } = useQuery({
    queryKey: ["golden-records-graph"],
    queryFn: async () => {
      const res = await api.get("/resolution/golden-records?limit=50");
      return res.data;
    }
  });

  const { data: edges } = useQuery({
    queryKey: ["identity-edges"],
    queryFn: async () => {
      try {
        const res = await api.get("/resolution/edges");
        return res.data;
      } catch {
        return [];
      }
    }
  });

  // ResizeObserver to track container size without usehooks-ts
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!goldenRecords) return;

    const nodes: any[] = [];
    const links: any[] = [];
    const addedNodeIds = new Set();

    const addNode = (node: any) => {
      if (!addedNodeIds.has(node.id)) {
        nodes.push(node);
        addedNodeIds.add(node.id);
      }
    };

    goldenRecords.forEach((gr: any) => {
      const goldenId = `golden-${gr.id}`;
      addNode({
        id: goldenId,
        label: gr.name || `Golden #${gr.id.substring(0, 6)}`,
        type: "golden",
        val: 3
      });

      (gr.source_systems || []).forEach((sys: string, i: number) => {
        const srcId = `src-${gr.id}-${i}`;
        addNode({
          id: srcId,
          label: sys.replace("_", " "),
          type: "source",
          system: sys,
          val: 1
        });
        links.push({
          source: goldenId,
          target: srcId,
          confidence: gr.match_confidence || 0.85,
          matchPhase: "RESOLVED"
        });
      });
    });

    (edges || []).forEach((e: any) => {
      const sourceId = `src-edge-${e.source_a_id}`;
      const targetId = `src-edge-${e.source_b_id}`;
      addNode({ id: sourceId, label: "Source A", type: "source", val: 1 });
      addNode({ id: targetId, label: "Source B", type: "source", val: 1 });
      
      links.push({
        source: sourceId,
        target: targetId,
        confidence: e.confidence_score || 0.8,
        matchPhase: e.match_phase || "UNKNOWN"
      });
    });

    setGraphData({ nodes, links });
  }, [goldenRecords, edges]);

  // Make the graph zoom to fit after data is loaded
  useEffect(() => {
    if (graphData.nodes.length > 0 && graphRef.current) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 50);
      }, 500);
    }
  }, [graphData]);

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    
    // Auto-center and zoom on selected node
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 500);
      graphRef.current.zoom(2.5, 500);
    }
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50);
    }
  }, []);

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="bg-white p-6 rounded-3xl card-shadow flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Network size={24} className="text-[#E2604B]" />
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">Identity Graph</h2>
            <p className="text-gray-500 text-sm mt-0.5">Interactive force-directed graph of resolved identities</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => graphRef.current?.zoomToFit(400, 50)}
            className="p-2 mr-4 bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            title="Zoom to Fit"
          >
            <Maximize2 size={18} />
          </button>
          <div className="flex items-center gap-3 mr-6 bg-gray-50 px-4 py-2 rounded-xl">
            {Object.entries(SYSTEM_COLORS).map(([sys, color]) => (
              <div key={sys} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></div>
                <span className="text-xs font-medium text-gray-600">{sys.replace("_", " ")}</span>
              </div>
            ))}
            <div className="w-px h-4 bg-gray-300 mx-2"></div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.6)]"></div>
              <span className="text-xs font-bold text-gray-700">Golden Record</span>
            </div>
          </div>
        </div>
      </div>

      <div 
        className="flex-1 bg-white rounded-3xl card-shadow overflow-hidden relative min-h-[600px] border border-gray-100" 
        ref={containerRef}
      >
        <div className="absolute inset-0 z-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:24px_24px] opacity-40"></div>
        
        {typeof window !== "undefined" && graphData.nodes.length > 0 && (
          <div className="absolute inset-0 z-10">
            <ForceGraph2D
              ref={graphRef}
              width={dimensions.width}
              height={dimensions.height}
              graphData={graphData}
              nodeLabel="label"
              onNodeClick={handleNodeClick}
              onBackgroundClick={handleBackgroundClick}
              cooldownTicks={100}
              d3VelocityDecay={0.3}
              nodeRelSize={6}
              linkColor={(link: any) => `rgba(226, 96, 75, ${link.confidence * 0.8})`}
              linkWidth={(link: any) => 1 + link.confidence * 4}
              linkDirectionalParticles={(link: any) => link.confidence > 0.8 ? 2 : 0}
              linkDirectionalParticleSpeed={0.005}
              linkDirectionalParticleWidth={3}
              linkDirectionalParticleColor={() => 'rgba(234, 179, 8, 0.6)'}
              nodeCanvasObjectMode={() => 'after'}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.label;
                const fontSize = 12/globalScale;
                ctx.font = `${node.type === 'golden' ? 'bold ' : ''}${fontSize}px Inter, sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = node.type === 'golden' ? '#1F2937' : '#4B5563';
                ctx.fillText(label, node.x, node.y + (node.type === 'golden' ? 14 : 10) + fontSize);
              }}
              nodeColor={(node: any) => {
                if (node.id === selectedNode?.id) return "#000000";
                if (node.type === 'golden') return "#EAB308";
                return SYSTEM_COLORS[node.system] || "#9CA3AF";
              }}
            />
          </div>
        )}
        
        {/* Selected node info panel */}
        {selectedNode && (
          <div className="absolute bottom-8 left-8 z-20 bg-white/95 backdrop-blur-xl rounded-2xl p-5 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.15)] border border-gray-100 min-w-[280px] animate-in slide-in-from-bottom-4 fade-in duration-300">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1.5">
              {selectedNode.type === "golden" ? "✨ Golden Record" : "📄 Source Record"}
            </p>
            <p className="text-lg font-bold text-gray-900 mb-3">{selectedNode.label}</p>
            {selectedNode.system && (
              <div className="flex items-center gap-2 mb-2 bg-gray-50 p-2 rounded-lg inline-flex">
                <div className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ backgroundColor: SYSTEM_COLORS[selectedNode.system] }}></div>
                <span className="text-sm font-medium text-gray-700">{selectedNode.system.replace("_", " ")}</span>
              </div>
            )}
            <p className="text-xs text-gray-500 mt-2 font-mono bg-gray-50 px-2 py-1 rounded">ID: {selectedNode.id}</p>
          </div>
        )}

        {!graphData.nodes.length && (
          <div className="absolute inset-0 z-20 flex items-center justify-center">
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 border-4 border-gray-200 border-t-[#E2604B] rounded-full animate-spin mb-4"></div>
              <p className="text-gray-500 font-medium">Computing identity graph...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
