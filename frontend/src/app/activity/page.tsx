"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { agent } from "@/lib/api";

interface ActivityItem {
  id: string;
  type: string;
  source: string;
  message: string;
  detail: string;
  time: string;
}

type FilterType = "all" | "background" | "chat";

let wsNextId = 0;

export default function ActivityPage() {
  const { user } = useAuth();
  const [connected, setConnected] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string>("idle");
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [filter, setFilter] = useState<FilterType>("all");
  const [paused, setPaused] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load historical events from API on mount
  useEffect(() => {
    agent
      .events({ limit: 500 })
      .then((data) => {
        const items: ActivityItem[] = data.map((e) => ({
          id: e.id,
          type: e.type,
          source: e.source,
          message: e.message,
          detail: e.detail,
          time: e.time ? new Date(e.time).toLocaleTimeString() : "",
        }));
        setActivities(items);
        setLoaded(true);
      })
      .catch(() => {
        setLoaded(true);
      });
  }, []);

  // Subscribe to WebSocket for live events (append to top)
  useEffect(() => {
    if (!user?.user_id) return;

    function connect() {
      const wsBase = process.env.NEXT_PUBLIC_WS_URL || `ws://localhost:8000`;
      const ws = new WebSocket(`${wsBase}/ws/${user!.user_id}`);

      ws.onopen = () => {
        setConnected(true);
        if (reconnectRef.current) {
          clearTimeout(reconnectRef.current);
          reconnectRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const type = msg.type as string;
          const data = msg.data as Record<string, unknown>;

          if (type === "agent:status") {
            setAgentStatus(data.status as string);
          }

          const source = (data.agent as string) || "nexus";
          const message = _formatMessage(type, data);
          const detail = _formatDetail(type, data);

          setActivities((prev) => [
            {
              id: `ws-${wsNextId++}`,
              type,
              source,
              message,
              detail,
              time: new Date().toLocaleTimeString(),
            },
            ...prev,
          ]);
        } catch {
          // ignore
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        reconnectRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
      wsRef.current = ws;
    }

    connect();
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [user?.user_id]);

  const handleToggle = async () => {
    try {
      if (paused) {
        await agent.resume();
        setPaused(false);
      } else {
        await agent.pause();
        setPaused(true);
      }
    } catch {
      /* ignore */
    }
  };

  const handleRunNow = async () => {
    try {
      await agent.runNow();
    } catch {
      /* ignore */
    }
  };

  const filtered = activities.filter((a) => {
    if (filter === "all") return true;
    if (filter === "background") return a.source !== "chat";
    return a.source === "chat";
  });

  const typeColor = (type: string) => {
    if (type.startsWith("event:")) return "text-blue-400";
    if (type.startsWith("person:")) return "text-emerald-400";
    if (type.startsWith("message:")) return "text-purple-400";
    if (type.startsWith("target:")) return "text-amber-400";
    if (type === "agent:status") return "text-gray-400";
    return "text-gray-500";
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                !connected
                  ? "bg-gray-600"
                  : agentStatus === "running"
                    ? "animate-pulse bg-green-500"
                    : "bg-yellow-500"
              }`}
            />
            <h1 className="text-lg font-semibold text-gray-100">Agent Activity</h1>
          </div>
          <span className="rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-400">
            {connected ? agentStatus : "disconnected"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunNow}
            className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
          >
            Run Now
          </button>
          <button
            onClick={handleToggle}
            className={`rounded px-3 py-1.5 text-xs font-medium text-white ${
              paused
                ? "bg-green-600 hover:bg-green-500"
                : "bg-yellow-600 hover:bg-yellow-500"
            }`}
          >
            {paused ? "Resume" : "Pause"}
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 border-b border-gray-800 px-6 py-2">
        {(["all", "background", "chat"] as FilterType[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition ${
              filter === f
                ? "bg-indigo-600/20 text-indigo-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {f === "background" ? "Background Agent" : f === "chat" ? "Chat Agent" : "All"}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-600">{filtered.length} events</span>
      </div>

      {/* Activity log */}
      <div className="flex-1 overflow-y-auto">
        {!loaded ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-gray-600">Loading activity...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <p className="text-sm text-gray-600">No activity yet</p>
            <p className="mt-1 text-xs text-gray-700">
              Agent events will appear here in real-time
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800/50">
            {filtered.map((a) => (
              <div
                key={a.id}
                className="flex items-start gap-4 px-6 py-3 transition hover:bg-gray-900/50"
              >
                <span className="mt-0.5 shrink-0 font-mono text-xs text-gray-600">
                  {a.time}
                </span>
                <span
                  className={`mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    a.source === "chat"
                      ? "bg-purple-500/10 text-purple-400"
                      : "bg-blue-500/10 text-blue-400"
                  }`}
                >
                  {a.source === "chat" ? "chat" : "bg"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className={`text-sm ${typeColor(a.type)}`}>{a.message}</p>
                  {a.detail && (
                    <p className="mt-0.5 truncate text-xs text-gray-600">{a.detail}</p>
                  )}
                </div>
                <span className="shrink-0 text-[10px] text-gray-700">{a.type}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Formatting helpers (mirror backend EVENT_LABELS) ─────────────── */

function _formatMessage(type: string, data: Record<string, unknown>): string {
  const fmts: Record<string, (d: Record<string, unknown>) => string> = {
    "event:discovered": (d) =>
      `Found event: ${_nested(d, "event", "title", "unknown")}`,
    "event:analyzed": (d) =>
      `Analyzed: ${_nested(d, "event", "title", "event")}`,
    "event:applied": (d) =>
      `Applied to: ${_nested(d, "event", "title", "event")}`,
    "event:scheduled": (d) =>
      `Scheduled: ${_nested(d, "event", "title", "event")}`,
    "person:discovered": (d) =>
      `Discovered person: ${_nested(d, "person", "name", "unknown")}`,
    "message:drafted": () => "Drafted a message",
    "message:sent": () => "Sent a message",
    "agent:status": (d) => {
      const tool = d.tool as string | undefined;
      return tool ? `Tool: ${tool}` : `Agent ${d.status}`;
    },
    "target:found": (d) =>
      `Target person matched: ${_nested(d, "target", "name", "")}`,
    "target:updated": (d) =>
      `Target updated: ${_nested(d, "target", "name", "")}`,
  };
  const fn = fmts[type];
  return fn ? fn(data) : type;
}

function _formatDetail(type: string, data: Record<string, unknown>): string {
  const fmts: Record<string, (d: Record<string, unknown>) => string> = {
    "event:discovered": (d) => `Count: ${d.count ?? "-"}`,
    "event:analyzed": (d) => `Score: ${d.score ?? "-"}`,
    "agent:status": (d) =>
      (d.detail as string) || (d.tool ? `Status: ${d.status}` : ""),
    "message:drafted": (d) =>
      `Channel: ${d.channel ?? "-"}, Type: ${d.type ?? "-"}`,
  };
  const fn = fmts[type];
  return fn ? fn(data) : "";
}

function _nested(
  d: Record<string, unknown>,
  key: string,
  sub: string,
  fallback: string,
): string {
  const obj = d[key];
  if (obj && typeof obj === "object" && sub in (obj as Record<string, unknown>)) {
    return String((obj as Record<string, string>)[sub]);
  }
  return fallback;
}
