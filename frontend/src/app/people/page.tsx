"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { graph } from "@/lib/api";
import type { GraphNode, GraphEdge, NetworkGraph } from "@/lib/types";
import { AddPersonModal, type PersonData } from "@/components/AddPersonModal";

/* ─── Constants ────────────────────────────────────── */

const ROLE_FILTERS = [
  { key: "all", label: "All" },
  { key: "engineer", label: "Engineers" },
  { key: "founder", label: "Founders" },
  { key: "product", label: "Product" },
  { key: "designer", label: "Designers" },
  { key: "investor", label: "Investors" },
  { key: "researcher", label: "Research" },
  { key: "devrel", label: "DevRel" },
];

/* ─── Force-directed graph layout ──────────────────── */

interface LayoutNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

function useForceLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number,
) {
  const [layoutNodes, setLayoutNodes] = useState<LayoutNode[]>([]);
  const frameRef = useRef<number>(0);
  const nodesRef = useRef<LayoutNode[]>([]);

  useEffect(() => {
    if (nodes.length === 0) return;

    const ln: LayoutNode[] = nodes.map((n, i) => ({
      ...n,
      x: width / 2 + Math.cos((i / nodes.length) * Math.PI * 2) * width * 0.35,
      y:
        height / 2 + Math.sin((i / nodes.length) * Math.PI * 2) * height * 0.35,
      vx: 0,
      vy: 0,
    }));
    nodesRef.current = ln;

    const idMap = new Map(ln.map((n, i) => [n.id, i]));
    let iteration = 0;
    const maxIterations = 200;

    const tick = () => {
      const ns = nodesRef.current;
      const centerX = width / 2;
      const centerY = height / 2;

      for (const n of ns) {
        n.vx *= 0.85;
        n.vy *= 0.85;
        // gravity to center
        n.vx += (centerX - n.x) * 0.003;
        n.vy += (centerY - n.y) * 0.003;
      }

      // repulsion
      for (let i = 0; i < ns.length; i++) {
        for (let j = i + 1; j < ns.length; j++) {
          const dx = ns[j].x - ns[i].x;
          const dy = ns[j].y - ns[i].y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
          const force = 800 / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          ns[i].vx -= fx;
          ns[i].vy -= fy;
          ns[j].vx += fx;
          ns[j].vy += fy;
        }
      }

      // attraction from edges
      for (const e of edges) {
        const si = idMap.get(e.source);
        const ti = idMap.get(e.target);
        if (si === undefined || ti === undefined) continue;
        const dx = ns[ti].x - ns[si].x;
        const dy = ns[ti].y - ns[si].y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const targetDist = 120 - (e.strength / 100) * 40;
        const force = (dist - targetDist) * 0.01;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        ns[si].vx += fx;
        ns[si].vy += fy;
        ns[ti].vx -= fx;
        ns[ti].vy -= fy;
      }

      // apply velocity & clamp — pin "me" to center
      const padding = 40;
      for (const n of ns) {
        if (n.is_self) {
          n.x = centerX;
          n.y = centerY;
          n.vx = 0;
          n.vy = 0;
          continue;
        }
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.max(padding, Math.min(width - padding, n.x));
        n.y = Math.max(padding, Math.min(height - padding, n.y));
      }

      setLayoutNodes([...ns]);
      iteration++;
      if (iteration < maxIterations) {
        frameRef.current = requestAnimationFrame(tick);
      }
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [nodes, edges, width, height]);

  return layoutNodes;
}

/* ─── Edge color & width from strength ─────────────── */

function edgeStyle(strength: number) {
  const w = Math.max(1, Math.min(4, strength / 25));
  const opacity = Math.max(0.15, Math.min(0.6, strength / 100));
  let color = "#d1d5db";
  if (strength >= 60) color = "#f97316";
  else if (strength >= 40) color = "#6366f1";
  else if (strength >= 20) color = "#a5b4fc";
  return { strokeWidth: w, stroke: color, opacity };
}

/* ─── Score badge color ────────────────────────────── */

function scoreColor(score: number): string {
  if (score >= 85) return "bg-orange-100 text-orange-700";
  if (score >= 70) return "bg-indigo-50 text-indigo-600";
  if (score >= 50) return "bg-gray-100 text-gray-600";
  return "bg-gray-50 text-gray-400";
}

/* ─── SNS Button ───────────────────────────────────── */

function SnsButton({
  href,
  label,
  color,
  icon,
}: {
  href: string;
  label: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-1.5 rounded-lg border border-black/[0.06] px-2.5 py-1.5 text-[11px] font-medium transition-all hover:shadow-sm"
      style={{ color }}
    >
      {icon}
      {label}
    </a>
  );
}

/* ─── Main Page Component ──────────────────────────── */

export default function PeoplePage() {
  const [data, setData] = useState<NetworkGraph | null>(null);
  const [ranked, setRanked] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [roleFilter, setRoleFilter] = useState("all");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [view, setView] = useState<"graph" | "list">("list");
  const [showAddModal, setShowAddModal] = useState(false);

  const loadData = useCallback(async (role?: string) => {
    try {
      const [network, rankedList] = await Promise.all([
        graph.network().catch(() => null),
        graph
          .ranked({ role: role === "all" ? undefined : role, limit: 50 })
          .catch(() => []),
      ]);
      setData(network as NetworkGraph | null);
      setRanked(rankedList as GraphNode[]);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await graph.seedEvent(
        "https://autonomous-agents-hackathon.devpost.com",
        "Autonomous Agents Hackathon",
      );
      await loadData();
    } catch {
      /* ignore */
    } finally {
      setSeeding(false);
    }
  };

  const handleFilterChange = (key: string) => {
    setRoleFilter(key);
    setLoading(true);
    loadData(key);
  };

  const handleAddPerson = async (person: PersonData) => {
    await graph.addPerson(person);
    await loadData();
  };

  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];
  const graphWidth = 700;
  const graphHeight = 460;
  const layoutNodes = useForceLayout(nodes, edges, graphWidth, graphHeight);
  const nodeMap = new Map(layoutNodes.map((n) => [n.id, n]));

  // If ranked API returned empty, build list from graph nodes
  const displayList =
    ranked.length > 0
      ? ranked
      : nodes
          .filter((n) => !n.is_self)
          .sort((a, b) => b.connection_score - a.connection_score)
          .map((n, i) => ({ ...n, rank: i + 1 }));

  const isEmpty = nodes.length === 0 && !loading;

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">People</h1>
          <p className="text-[13px] text-gray-400">
            {data?.stats.total_people ?? 0} people ·{" "}
            {data?.stats.total_connections ?? 0} connections
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex rounded-xl border border-black/[0.04] bg-white p-0.5">
            {(["graph", "list"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`rounded-lg px-3 py-1.5 text-[11px] font-medium transition-all ${
                  view === v
                    ? "bg-[#1a1a1a] text-white shadow-sm"
                    : "text-gray-400 hover:text-gray-600"
                }`}
              >
                {v === "graph" ? "Graph" : "List"}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="rounded-xl border border-black/[0.08] bg-white px-4 py-2 text-[12px] font-medium text-gray-600 shadow-sm transition-all hover:bg-gray-50"
          >
            + Add Person
          </button>
        </div>
      </div>

      {/* Add Person Modal */}
      <AddPersonModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddPerson}
      />

      {/* Role Filters */}
      <div className="mb-5 flex gap-1.5 overflow-x-auto">
        {ROLE_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => handleFilterChange(f.key)}
            className={`shrink-0 rounded-full px-3.5 py-1.5 text-[11px] font-medium transition-all duration-200 ${
              roleFilter === f.key
                ? "bg-[#1a1a1a] text-white shadow-sm"
                : "text-gray-400 hover:bg-black/[0.04] hover:text-gray-600"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-[500px] items-center justify-center">
          <div className="text-sm text-gray-400">Loading graph...</div>
        </div>
      ) : isEmpty ? (
        <EmptyState onSeed={handleSeed} seeding={seeding} />
      ) : (
        <div className="flex gap-4">
          {/* Left: Graph or List */}
          <div className="flex-1 min-w-0">
            {view === "graph" ? (
              <GraphView
                nodes={layoutNodes}
                edges={edges}
                nodeMap={nodeMap}
                width={graphWidth}
                height={graphHeight}
                selected={selectedNode}
                onSelect={setSelectedNode}
              />
            ) : (
              <ListView
                ranked={displayList}
                onSelect={setSelectedNode}
                selected={selectedNode}
              />
            )}
          </div>

          {/* Right: Detail panel */}
          <div className="w-[280px] shrink-0">
            {selectedNode ? (
              <PersonDetail
                node={selectedNode}
                edges={edges}
                nodeMap={nodeMap}
                onClose={() => setSelectedNode(null)}
              />
            ) : (
              <RankedSidebar
                ranked={displayList.slice(0, 8)}
                onSelect={setSelectedNode}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Graph View ───────────────────────────────────── */

function GraphView({
  nodes,
  edges,
  nodeMap,
  width,
  height,
  selected,
  onSelect,
}: {
  nodes: LayoutNode[];
  edges: GraphEdge[];
  nodeMap: Map<string, LayoutNode>;
  width: number;
  height: number;
  selected: GraphNode | null;
  onSelect: (n: GraphNode | null) => void;
}) {
  return (
    <div className="rounded-2xl border border-black/[0.04] bg-white shadow-[0_1px_3px_rgba(0,0,0,0.04)] overflow-hidden">
      <svg
        width="100%"
        viewBox={`0 0 ${width} ${height}`}
        className="cursor-pointer"
      >
        {/* Edges */}
        {edges.map((e, i) => {
          const s = nodeMap.get(e.source);
          const t = nodeMap.get(e.target);
          if (!s || !t) return null;
          const style = edgeStyle(e.strength);
          const isHighlighted =
            selected && (selected.id === e.source || selected.id === e.target);
          return (
            <line
              key={i}
              x1={s.x}
              y1={s.y}
              x2={t.x}
              y2={t.y}
              stroke={style.stroke}
              strokeWidth={
                isHighlighted ? style.strokeWidth + 1.5 : style.strokeWidth
              }
              opacity={selected ? (isHighlighted ? 0.8 : 0.08) : style.opacity}
              strokeLinecap="round"
            />
          );
        })}
        {/* Nodes */}
        {nodes.map((n) => {
          const isSelf = n.is_self;
          const r = isSelf ? 26 : 10 + (n.connection_score / 100) * 12;
          const isSelected = selected?.id === n.id;
          const isConnected =
            selected &&
            edges.some(
              (e) =>
                (e.source === selected.id && e.target === n.id) ||
                (e.target === selected.id && e.source === n.id),
            );
          const dimmed = selected && !isSelected && !isConnected && !isSelf;
          return (
            <g
              key={n.id}
              onClick={() =>
                isSelf ? undefined : onSelect(isSelected ? null : n)
              }
              className="transition-all duration-200"
              opacity={dimmed ? 0.2 : 1}
              style={{ cursor: isSelf ? "default" : "pointer" }}
            >
              {/* "Me" outer ring */}
              {isSelf && (
                <>
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={r + 10}
                    fill="#f97316"
                    opacity={0.08}
                  />
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={r + 5}
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="1.5"
                    strokeDasharray="4 3"
                    opacity={0.4}
                  >
                    <animateTransform
                      attributeName="transform"
                      type="rotate"
                      from={`0 ${n.x} ${n.y}`}
                      to={`360 ${n.x} ${n.y}`}
                      dur="20s"
                      repeatCount="indefinite"
                    />
                  </circle>
                </>
              )}
              {/* Selection glow */}
              {isSelected && !isSelf && (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={r + 6}
                  fill={n.avatar_color}
                  opacity={0.15}
                />
              )}
              {/* Circle */}
              <circle
                cx={n.x}
                cy={n.y}
                r={r}
                fill={isSelf ? "#f97316" : n.avatar_color}
                stroke={isSelected ? "#1a1a1a" : isSelf ? "#f97316" : "white"}
                strokeWidth={isSelf ? 3 : isSelected ? 2.5 : 2}
                className="transition-all duration-200 hover:brightness-110"
              />
              {/* Initials / Me label */}
              <text
                x={n.x}
                y={n.y + 1}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="white"
                fontSize={isSelf ? "11" : "9"}
                fontWeight="700"
                className="pointer-events-none select-none"
              >
                {isSelf
                  ? "ME"
                  : n.name
                      .split(" ")
                      .map((w) => w[0])
                      .join("")
                      .slice(0, 2)}
              </text>
              {/* Name label */}
              <text
                x={n.x}
                y={n.y + r + 12}
                textAnchor="middle"
                fill={isSelf ? "#f97316" : "#374151"}
                fontSize={isSelf ? "10" : "8"}
                fontWeight={isSelf ? "800" : "600"}
                className="pointer-events-none select-none"
              >
                {isSelf ? "Me" : n.name.split(" ")[0]}
              </text>
            </g>
          );
        })}
      </svg>
      {/* Legend */}
      <div className="flex items-center justify-center gap-4 border-t border-black/[0.04] px-4 py-2 text-[10px] text-gray-400">
        <span className="flex items-center gap-1.5">
          <span className="h-[3px] w-4 rounded bg-[#f97316]" /> Strong (60+)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-[2px] w-4 rounded bg-[#6366f1]" /> Medium (40+)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-[1px] w-4 rounded bg-[#d1d5db]" /> Weak
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full bg-gray-300" />{" "}
          Node = person
        </span>
      </div>
    </div>
  );
}

/* ─── List View ────────────────────────────────────── */

function ListView({
  ranked,
  onSelect,
  selected,
}: {
  ranked: GraphNode[];
  onSelect: (n: GraphNode) => void;
  selected: GraphNode | null;
}) {
  return (
    <div className="space-y-2 stagger-children">
      {ranked.map((p, i) => (
        <button
          key={p.id}
          onClick={() => onSelect(p)}
          className={`flex w-full items-center gap-3 rounded-2xl border p-3.5 text-left transition-all duration-200 ${
            selected?.id === p.id
              ? "border-[#1a1a1a]/10 bg-white shadow-[0_4px_16px_rgba(0,0,0,0.06)]"
              : "border-black/[0.04] bg-white shadow-[0_1px_3px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]"
          }`}
        >
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-[10px] font-bold text-gray-400 tabular-nums">
            {i + 1}
          </span>
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-bold text-white"
            style={{ background: p.avatar_color }}
          >
            {p.name
              .split(" ")
              .map((w) => w[0])
              .join("")
              .slice(0, 2)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-semibold text-gray-900 truncate">
              {p.name}
            </p>
            <p className="text-[11px] text-gray-400 truncate">
              {p.title}
              {p.title && p.company ? " at " : ""}
              {p.company}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums ${scoreColor(p.connection_score)}`}
            >
              {p.connection_score}
            </span>
            <div className="flex gap-1">
              {p.topics?.slice(0, 2).map((t) => (
                <span
                  key={t}
                  className="rounded-full bg-[#F7F7F4] px-1.5 py-0.5 text-[8px] text-gray-400"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

/* ─── Person Detail Panel ──────────────────────────── */

function PersonDetail({
  node,
  edges,
  nodeMap,
  onClose,
}: {
  node: GraphNode;
  edges: GraphEdge[];
  nodeMap: Map<string, { name: string; avatar_color: string }>;
  onClose: () => void;
}) {
  const connections = edges
    .filter((e) => e.source === node.id || e.target === node.id)
    .map((e) => {
      const otherId = e.source === node.id ? e.target : e.source;
      const other = nodeMap.get(otherId);
      return {
        ...e,
        otherId,
        otherName: other?.name ?? "Unknown",
        otherColor: other?.avatar_color ?? "#ccc",
      };
    })
    .sort((a, b) => b.strength - a.strength);

  return (
    <div className="rounded-2xl border border-black/[0.04] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] animate-fade-in-up">
      <div className="mb-3 flex items-start justify-between">
        <div
          className="flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-bold text-white"
          style={{ background: node.avatar_color }}
        >
          {node.name
            .split(" ")
            .map((w) => w[0])
            .join("")
            .slice(0, 2)}
        </div>
        <button
          onClick={onClose}
          className="text-gray-300 hover:text-gray-500 text-lg leading-none"
        >
          &times;
        </button>
      </div>
      <h3 className="text-[15px] font-bold text-gray-900">{node.name}</h3>
      <p className="text-[12px] text-gray-400">
        {node.title}
        {node.title && node.company ? " at " : ""}
        {node.company}
      </p>
      <div className="mt-2">
        <span
          className={`inline-block rounded-full px-2.5 py-1 text-[11px] font-bold tabular-nums ${scoreColor(node.connection_score)}`}
        >
          Score: {node.connection_score}
        </span>
      </div>

      {/* Topics */}
      {node.topics && node.topics.length > 0 && (
        <div className="mt-3">
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-400">
            Topics
          </p>
          <div className="flex flex-wrap gap-1">
            {node.topics.map((t) => (
              <span
                key={t}
                className="rounded-full bg-[#F7F7F4] px-2 py-0.5 text-[10px] font-medium text-gray-500"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* SNS Links */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {node.linkedin && (
          <SnsButton
            href={node.linkedin}
            label="LinkedIn"
            color="#0a66c2"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.3 6.5a1.78 1.78 0 01-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0013 14.19V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.86 3.36 3.66z" />
              </svg>
            }
          />
        )}
        {node.twitter && (
          <SnsButton
            href={`https://x.com/${node.twitter.replace("@", "")}`}
            label="X"
            color="#000"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            }
          />
        )}
        {node.facebook && (
          <SnsButton
            href={`https://facebook.com/${node.facebook}`}
            label="Facebook"
            color="#1877f2"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
              </svg>
            }
          />
        )}
        {node.instagram && (
          <SnsButton
            href={`https://instagram.com/${node.instagram}`}
            label="Insta"
            color="#e4405f"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
              </svg>
            }
          />
        )}
        {node.github && (
          <SnsButton
            href={`https://github.com/${node.github}`}
            label="GitHub"
            color="#24292f"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            }
          />
        )}
        {node.website && (
          <SnsButton
            href={
              node.website.startsWith("http")
                ? node.website
                : `https://${node.website}`
            }
            label="Web"
            color="#059669"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="2" y1="12" x2="22" y2="12" />
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            }
          />
        )}
        {node.email && (
          <SnsButton
            href={`mailto:${node.email}`}
            label="Email"
            color="#6b7280"
            icon={
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
              </svg>
            }
          />
        )}
      </div>

      {/* Connections */}
      {connections.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-gray-400">
            Connections ({connections.length})
          </p>
          <div className="space-y-1.5">
            {connections.slice(0, 6).map((c) => (
              <div key={c.otherId} className="flex items-center gap-2">
                <div
                  className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[7px] font-bold text-white"
                  style={{ background: c.otherColor }}
                >
                  {c.otherName
                    .split(" ")
                    .map((w: string) => w[0])
                    .join("")
                    .slice(0, 2)}
                </div>
                <span className="flex-1 truncate text-[11px] text-gray-600">
                  {c.otherName}
                </span>
                <div
                  className="h-1 rounded-full"
                  style={{
                    width: `${Math.max(16, c.strength)}px`,
                    background:
                      c.strength >= 60
                        ? "#f97316"
                        : c.strength >= 40
                          ? "#6366f1"
                          : "#d1d5db",
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Ranked Sidebar ───────────────────────────────── */

function RankedSidebar({
  ranked,
  onSelect,
}: {
  ranked: GraphNode[];
  onSelect: (n: GraphNode) => void;
}) {
  return (
    <div className="rounded-2xl border border-black/[0.04] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <h3 className="mb-3 text-[12px] font-semibold uppercase tracking-widest text-gray-400">
        Top Connections
      </h3>
      <div className="space-y-2">
        {ranked.map((p, i) => (
          <button
            key={p.id}
            onClick={() => onSelect(p)}
            className="flex w-full items-center gap-2.5 rounded-xl p-2 text-left transition-all hover:bg-[#F7F7F4]"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-gray-100 text-[9px] font-bold text-gray-400 tabular-nums">
              {i + 1}
            </span>
            <div
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
              style={{ background: p.avatar_color }}
            >
              {p.name
                .split(" ")
                .map((w) => w[0])
                .join("")
                .slice(0, 2)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[12px] font-semibold text-gray-800">
                {p.name}
              </p>
              <p className="truncate text-[10px] text-gray-400">{p.company}</p>
            </div>
            <span
              className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold tabular-nums ${scoreColor(p.connection_score)}`}
            >
              {p.connection_score}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─── Empty State ──────────────────────────────────── */

function EmptyState({
  onSeed,
  seeding,
}: {
  onSeed: () => void;
  seeding: boolean;
}) {
  return (
    <div className="flex h-[500px] flex-col items-center justify-center text-center animate-fade-in">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F7F7F4] text-2xl">
        🕸️
      </div>
      <h2 className="text-lg font-bold text-gray-900">No connections yet</h2>
      <p className="mt-1 max-w-xs text-[13px] text-gray-400">
        Seed your first event to discover people and build your network graph.
      </p>
      <button
        onClick={onSeed}
        disabled={seeding}
        className="mt-4 rounded-xl bg-[#1a1a1a] px-5 py-2.5 text-[13px] font-medium text-white shadow-sm transition-all hover:bg-gray-800 disabled:opacity-50"
      >
        {seeding ? "Seeding..." : "Seed: Autonomous Agents Hackathon"}
      </button>
    </div>
  );
}
