"use client";

import { useEffect, useRef, useState } from "react";

interface GraphNode {
  id: string; title: string; tags: string[];
  x?: number; y?: number; vx?: number; vy?: number;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  link_type?: string;
}

const EDGE_COLORS: Record<string, string> = {
  supports: "#16a34a",
  contradicts: "#dc2626",
  depends_on: "#f59e0b",
  relates_to: "#d1d5db",
};

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

function forceSimulation(nodes: GraphNode[], edges: GraphEdge[], width: number, height: number) {
  const centerX = width / 2;
  const centerY = height / 2;
  const alpha = { current: 1 };
  const decay = 0.98;

  nodes.forEach((n) => {
    n.x = centerX + (Math.random() - 0.5) * 200;
    n.y = centerY + (Math.random() - 0.5) * 200;
    n.vx = 0; n.vy = 0;
  });

  for (let iter = 0; iter < 200 && alpha.current > 0.001; iter++) {
    alpha.current *= decay;

    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      let fx = 0, fy = 0;

      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        const dx = (b.x || 0) - (a.x || 0);
        const dy = (b.y || 0) - (a.y || 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = 500 / (dist * dist);
        const fx2 = (dx / dist) * force;
        const fy2 = (dy / dist) * force;
        fx -= fx2; fy -= fy2;
        (b.vx = (b.vx || 0) + fx2);
        (b.vy = (b.vy || 0) + fy2);
      }

      fx += (centerX - (a.x || 0)) * 0.005;
      fy += (centerY - (a.y || 0)) * 0.005;

      (a.vx = ((a.vx || 0) + fx) * 0.6);
      (a.vy = ((a.vy || 0) + fy) * 0.6);
      a.x = (a.x || 0) + (a.vx || 0);
      a.y = (a.y || 0) + (a.vy || 0);
      a.x = Math.max(30, Math.min(width - 30, a.x));
      a.y = Math.max(30, Math.min(height - 30, a.y));
    }
  }

  const edgeMap = new Map<string, Set<string>>();
  for (const e of edges) {
    const s = typeof e.source === "string" ? e.source : e.source.id;
    const t = typeof e.target === "string" ? e.target : e.target.id;
    if (!edgeMap.has(s)) edgeMap.set(s, new Set());
    if (!edgeMap.has(t)) edgeMap.set(t, new Set());
    edgeMap.get(s)!.add(t);
    edgeMap.get(t)!.add(s);
  }

  // spring attraction for linked nodes
  for (let iter = 0; iter < 10; iter++) {
    for (const e of edges) {
      const s = typeof e.source === "string" ? nodes.find((n) => n.id === e.source)! : e.source;
      const t = typeof e.target === "string" ? nodes.find((n) => n.id === e.target)! : e.target;
      if (!s || !t) continue;
      const dx = (t.x || 0) - (s.x || 0);
      const dy = (t.y || 0) - (s.y || 0);
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 100;
      const force = (dist - targetDist) * 0.01;
      const f2x = (dx / dist) * force * 0.5;
      const f2y = (dy / dist) * force * 0.5;
      s.x = (s.x || 0) + f2x;
      s.y = (s.y || 0) + f2y;
      t.x = (t.x || 0) - f2x;
      t.y = (t.y || 0) - f2y;
    }
  }
}

export function KnowledgeGraph({
  data,
  onSelect,
}: {
  data: GraphData | null;
  onSelect?: (id: string) => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [positions, setPositions] = useState<GraphNode[]>([]);
  const [computed, setComputed] = useState(false);

  useEffect(() => {
    if (!data || data.nodes.length === 0) return;
    const nodes = data.nodes.map((n) => ({ ...n }));
    forceSimulation(nodes, data.edges, 800, 500);
    setPositions(nodes);
    setComputed(true);
  }, [data]);

  if (!data || data.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] border rounded-xl bg-muted/20 text-muted-foreground text-sm">
        No notes or links to visualize yet.
      </div>
    );
  }

  const nodeMap = new Map(positions.map((n) => [n.id, n]));
  const edgeLines = data.edges.map((e, i) => {
    const s = typeof e.source === "string" ? nodeMap.get(e.source) : e.source as GraphNode;
    const t = typeof e.target === "string" ? nodeMap.get(e.target) : e.target as GraphNode;
    if (!s || !t) return null;
    const lt = e.link_type || "relates_to";
    const color = EDGE_COLORS[lt] || EDGE_COLORS.relates_to;
    return (
      <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y}
        stroke={color} strokeWidth={lt === "relates_to" ? 1 : 2} />
    );
  });

  return (
    <div className="border rounded-xl overflow-hidden bg-background">
      <div className="px-4 py-2 border-b bg-muted/30">
        <span className="text-sm font-medium">Knowledge Graph</span>
        <span className="text-xs text-muted-foreground ml-2">
          {data.nodes.length} notes, {data.edges.length} links
        </span>
      </div>
      <svg ref={svgRef} viewBox="0 0 800 500"
        className="w-full h-[400px] touch-none">
        {edgeLines}
        {positions.map((n) => {
          const isHovered = hovered === n.id;
          const r = isHovered ? 10 : 7;
          return (
            <g key={n.id} className="cursor-pointer"
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => onSelect?.(n.id)}>
              <circle cx={n.x} cy={n.y} r={r}
                fill={isHovered ? "#6366f1" : "#a5b4fc"} />
              {isHovered && (
                <>
                  <text x={(n.x || 0) + 14} y={(n.y || 0) + 4}
                    className="text-xs fill-foreground font-medium"
                    style={{ fontSize: "11px" }}>
                    {n.title.length > 25 ? n.title.slice(0, 25) + "..." : n.title}
                  </text>
                  {n.tags.length > 0 && (
                    <text x={(n.x || 0) + 14} y={(n.y || 0) + 18}
                      className="fill-muted-foreground"
                      style={{ fontSize: "9px" }}>
                      {n.tags.join(", ")}
                    </text>
                  )}
                </>
              )}
            </g>
          );
        })}
      </svg>
      <div className="flex gap-4 px-4 py-2 border-t bg-muted/20 text-xs text-muted-foreground">
        {Object.entries(EDGE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1">
            <span className="w-3 h-0.5 inline-block rounded" style={{ backgroundColor: color }} />
            {type.replace("_", " ")}
          </span>
        ))}
      </div>
    </div>
  );
}
