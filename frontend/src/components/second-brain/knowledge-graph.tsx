"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import * as d3 from "d3";

interface GraphNode {
  id: string; title: string; tags: string[];
}
interface GraphEdge {
  source: string;
  target: string;
  link_type?: string;
}
interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string; title: string; tags: string[];
}
interface SimEdge extends d3.SimulationLinkDatum<SimNode> {
  link_type?: string;
}

const EDGE_COLORS: Record<string, string> = {
  supports: "#16a34a",
  contradicts: "#dc2626",
  depends_on: "#f59e0b",
  relates_to: "#94a3b8",
};
const TAG_COLORS = [
  "#6366f1", "#ec4899", "#14b8a6", "#f97316", "#8b5cf6",
  "#06b6d4", "#84cc16", "#f43f5e", "#3b82f6", "#eab308",
];

export function KnowledgeGraph({ data }: { data: GraphData | null }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simRef = useRef<d3.Simulation<SimNode, SimEdge> | null>(null);
  const [selectedTag, setSelectedTag] = useState("");
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const allTags = useMemo(() => {
    if (!data) return [];
    const tags = new Set<string>();
    data.nodes.forEach((n) => n.tags?.forEach((t) => tags.add(t)));
    return Array.from(tags).sort();
  }, [data]);

  // Filter data
  const { simNodes, simEdges } = useMemo(() => {
    if (!data) return { simNodes: [], simEdges: [] };
    if (!selectedTag) {
      return {
        simNodes: data.nodes.map((n) => ({ ...n })),
        simEdges: data.edges.map((e) => ({ ...e })),
      };
    }
    const nodeIds = new Set(
      data.nodes.filter((n) => n.tags?.includes(selectedTag)).map((n) => n.id)
    );
    return {
      simNodes: data.nodes.filter((n) => nodeIds.has(n.id)).map((n) => ({ ...n })),
      simEdges: data.edges
        .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
        .map((e) => ({ ...e })),
    };
  }, [data, selectedTag]);

  const toggleType = useCallback((type: string) => {
    setHiddenTypes((prev) => {
      const next = new Set(prev);
      next.has(type) ? next.delete(type) : next.add(type);
      return next;
    });
  }, []);

  // D3 simulation
  useEffect(() => {
    if (!svgRef.current || simNodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    const width = containerRef.current?.clientWidth || 800;
    const height = 500;
    svg.selectAll("*").remove();

    const g = svg.append("g");

    // Zoom + pan
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on("zoom", (event) => g.attr("transform", event.transform.toString()));
    svg.call(zoom);

    // Force simulation
    const simulation = d3.forceSimulation<SimNode>(simNodes)
      .force("link", d3.forceLink<SimNode, SimEdge>(simEdges).id((d) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(20));
    simRef.current = simulation;

    // Edges
    const link = g.append("g").selectAll<SVGLineElement, SimEdge>("line")
      .data(simEdges)
      .join("line")
      .attr("stroke", (d) => EDGE_COLORS[d.link_type || "relates_to"] || EDGE_COLORS.relates_to)
      .attr("stroke-width", (d) => (d.link_type === "relates_to" ? 1 : 2))
      .attr("opacity", 0.6);

    // Nodes
    const node = g.append("g").selectAll<SVGGElement, SimNode>("g")
      .data(simNodes)
      .join("g")
      .call(
        d3.drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
      );

    node.append("circle")
      .attr("r", 7)
      .attr("fill", (d) => {
        const tag = d.tags?.[0];
        return tag ? TAG_COLORS[allTags.indexOf(tag) % TAG_COLORS.length] : "#a5b4fc";
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 0);

    node.append("title")
      .text((d) => `${d.title}\n${(d.tags || []).join(", ")}`);

    node.on("click", (_event, d) => setSelectedNode(d.id));

    // Hover effects
    node.on("mouseenter", function () {
      d3.select(this).select("circle")
        .transition().duration(150).attr("r", 10).attr("stroke-width", 2);
    });
    node.on("mouseleave", function () {
      d3.select(this).select("circle")
        .transition().duration(150).attr("r", 7).attr("stroke-width", 0);
    });

    // Labels (visible on larger graphs only when zoomed)
    node.append("text")
      .attr("dx", 12).attr("dy", 4)
      .text((d) => d.title.length > 20 ? d.title.slice(0, 20) + "..." : d.title)
      .style("font-size", "10px")
      .style("fill", "currentColor")
      .style("opacity", 0);

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x!)
        .attr("y1", (d) => (d.source as SimNode).y!)
        .attr("x2", (d) => (d.target as SimNode).x!)
        .attr("y2", (d) => (d.target as SimNode).y!);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [simNodes, simEdges, allTags]);

  // Update edge visibility when hiddenTypes changes
  useEffect(() => {
    if (!simEdges.length) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll<SVGLineElement, SimEdge>("line")
      .attr("opacity", (d) =>
        hiddenTypes.has(d.link_type || "relates_to") ? 0 : 0.6
      );
  }, [hiddenTypes, simEdges]);

  if (!data || data.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] border rounded-xl bg-muted/20 text-muted-foreground text-sm">
        No notes or links to visualize yet.
      </div>
    );
  }

  return (
    <div className="border rounded-xl overflow-hidden bg-background">
      {/* Header */}
      <div className="px-4 py-2 border-b bg-muted/30 flex items-center gap-3 flex-wrap">
        <span className="text-sm font-medium">Knowledge Graph</span>
        <span className="text-xs text-muted-foreground">
          {simNodes.length} notes, {simEdges.length} links
        </span>
        {selectedNode && (
          <span className="text-xs text-brand ml-2">
            Selected: {simNodes.find((n) => n.id === selectedNode)?.title?.slice(0, 30)}
            <button onClick={() => setSelectedNode(null)} className="ml-2 text-muted-foreground hover:text-foreground">✕</button>
          </span>
        )}
        {allTags.length > 0 && (
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="ml-auto text-xs border rounded px-2 py-1 bg-background"
          >
            <option value="">All tags</option>
            {allTags.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        )}
      </div>

      {/* SVG */}
      <div ref={containerRef}>
        <svg ref={svgRef} viewBox={`0 0 ${containerRef.current?.clientWidth || 800} 500`}
          className="w-full h-[450px]" />
      </div>

      {/* Legend */}
      <div className="flex gap-3 px-4 py-2 border-t bg-muted/20 text-xs text-muted-foreground flex-wrap items-center">
        {Object.entries(EDGE_COLORS).map(([type, color]) => {
          const hidden = hiddenTypes.has(type);
          return (
            <button key={type} onClick={() => toggleType(type)}
              className={`flex items-center gap-1 hover:opacity-100 transition-opacity ${hidden ? "opacity-30 line-through" : "opacity-80"}`}>
              <span className="w-3 h-0.5 inline-block rounded"
                style={{ backgroundColor: color }} />
              {type.replace("_", " ")}
            </button>
          );
        })}
        {selectedTag && (
          <button onClick={() => setSelectedTag("")}
            className="ml-auto text-brand hover:underline text-[11px]">
            Clear filter
          </button>
        )}
      </div>
    </div>
  );
}
