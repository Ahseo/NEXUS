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

          const source = (data.agent as string) || "wingman";
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

  return (
    <div className="flex h-full flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-black/[0.04] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full transition-all duration-500 ${
                !connected
                  ? "bg-gray-300"
                  : agentStatus === "running"
                    ? "bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.4)] animate-pulse"
                    : "bg-gray-400"
              }`}
            />
            <h1 className="text-[15px] font-semibold text-gray-900">Activity</h1>
          </div>
          <span className="rounded-full bg-[#F7F7F4] px-2.5 py-0.5 text-[11px] font-medium text-gray-400">
            {connected ? agentStatus : "disconnected"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunNow}
            className="rounded-xl bg-[#1a1a1a] px-3.5 py-1.5 text-[12px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]"
          >
            Run Now
          </button>
          <button
            onClick={handleToggle}
            className={`rounded-xl px-3.5 py-1.5 text-[12px] font-medium transition-all duration-200 active:scale-[0.97] ${
              paused
                ? "bg-[#1a1a1a] text-white hover:bg-[#333]"
                : "border border-black/[0.06] bg-white text-gray-500 hover:bg-gray-50"
            }`}
          >
            {paused ? "Resume" : "Pause"}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-1.5 border-b border-black/[0.04] px-6 py-2.5">
        {(["all", "background", "chat"] as FilterType[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-[12px] font-medium capitalize transition-all duration-200 ${
              filter === f
                ? "bg-[#1a1a1a] text-white shadow-sm"
                : "text-gray-400 hover:bg-black/[0.04] hover:text-gray-600"
            }`}
          >
            {f === "background" ? "Background" : f === "chat" ? "Chat" : "All"}
          </button>
        ))}
        <span className="ml-auto text-[11px] text-gray-300 tabular-nums">{filtered.length} events</span>
      </div>

      {/* Log */}
      <div className="flex-1 overflow-y-auto">
        {!loaded ? (
          <div className="space-y-2 p-4">
            {[1, 2, 3, 4, 5].map((n) => (
              <div
                key={n}
                className="h-14 rounded-xl bg-white/60 animate-pulse"
                style={{ animationDelay: `${n * 60}ms` }}
              />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center animate-fade-in">
            <p className="text-sm text-gray-400">No activity yet</p>
            <p className="mt-1 text-[12px] text-gray-300">
              Events will appear here in real-time
            </p>
          </div>
        ) : (
          <div className="divide-y divide-black/[0.03] stagger-children">
            {filtered.map((a) => (
              <div
                key={a.id}
                className="flex items-start gap-4 px-6 py-3 transition-colors duration-200 hover:bg-white/50"
              >
                <span className="mt-0.5 shrink-0 font-mono text-[11px] tabular-nums text-gray-300">
                  {a.time}
                </span>
                <span
                  className={`mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    a.source === "chat"
                      ? "bg-gray-100 text-gray-500"
                      : "bg-[#F7F7F4] text-gray-400"
                  }`}
                >
                  {a.source === "chat" ? "chat" : "bg"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] text-gray-700">{a.message}</p>
                  {a.detail && (
                    <p className="mt-0.5 truncate text-[11px] text-gray-400">{a.detail}</p>
                  )}
                </div>
                <span className="shrink-0 text-[10px] text-gray-300">{a.type}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Formatting helpers ─────────────────────────────── */

function _formatMessage(type: string, data: Record<string, unknown>): string {
  const fmts: Record<string, (d: Record<string, unknown>) => string> = {
    "event:discovered": (d) => `Found event: ${_nested(d, "event", "title", "unknown")}`,
    "event:analyzed": (d) => `Analyzed: ${_nested(d, "event", "title", "event")}`,
    "event:applied": (d) => `Applied to: ${_nested(d, "event", "title", "event")}`,
    "event:scheduled": (d) => `Scheduled: ${_nested(d, "event", "title", "event")}`,
    "person:discovered": (d) => `Discovered person: ${_nested(d, "person", "name", "unknown")}`,
    "message:drafted": () => "Drafted a message",
    "message:sent": () => "Sent a message",
    "agent:status": (d) => {
      const tool = d.tool as string | undefined;
      return tool ? `Tool: ${tool}` : `Agent ${d.status}`;
    },
    "target:found": (d) => `Target matched: ${_nested(d, "target", "name", "")}`,
    "target:updated": (d) => `Target updated: ${_nested(d, "target", "name", "")}`,
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
