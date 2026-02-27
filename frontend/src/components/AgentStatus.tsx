"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthProvider";

interface ActivityItem {
  id: number;
  type: string;
  message: string;
  time: string;
}

const EVENT_LABELS: Record<string, (data: Record<string, unknown>) => string> = {
  "event:discovered": (d) =>
    `Found: ${(d.event as Record<string, string>)?.title ?? "event"}`,
  "event:analyzed": (d) =>
    `Scored ${(d.event as Record<string, string>)?.title ?? "event"}: ${d.score}`,
  "event:applied": (d) =>
    `Applied to ${(d.event as Record<string, string>)?.title ?? "event"}`,
  "event:scheduled": (d) =>
    `Scheduled ${(d.event as Record<string, string>)?.title ?? "event"}`,
  "person:discovered": (d) =>
    `Found: ${(d.person as Record<string, string>)?.name ?? "person"}`,
  "message:drafted": () => "Drafted message",
  "message:sent": () => "Sent message",
  "agent:status": (d) => {
    const tool = d.tool as string | undefined;
    return tool ? `Tool: ${tool}` : `Agent ${d.status}`;
  },
  "target:found": (d) =>
    `Target: ${(d.target as Record<string, string>)?.name ?? ""}`,
  "target:updated": (d) =>
    `Target updated: ${(d.target as Record<string, string>)?.name ?? ""}`,
};

let nextId = 0;

export default function AgentStatus() {
  const { user } = useAuth();
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<string>("idle");
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

          // Only show background agent events (not chat)
          const source = (data.agent as string) || "nexus";
          if (source === "chat") return;

          if (type === "agent:status") {
            setStatus(data.status as string);
          }

          const labelFn = EVENT_LABELS[type];
          const message = labelFn ? labelFn(data) : type;

          setActivities((prev) => [
            {
              id: nextId++,
              type,
              message,
              time: new Date().toLocaleTimeString(),
            },
            ...prev.slice(0, 9), // keep last 10 in sidebar
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

  return (
    <div className="space-y-2">
      {/* Status indicator + expand link */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              !connected
                ? "bg-gray-600"
                : status === "running"
                  ? "animate-pulse bg-green-500"
                  : "bg-yellow-500"
            }`}
          />
          <span className="text-xs text-gray-400">
            {!connected ? "Disconnected" : `Agent ${status}`}
          </span>
        </div>
        <Link
          href="/activity"
          className="text-[10px] text-gray-600 transition hover:text-indigo-400"
          title="View full activity log"
        >
          Expand
        </Link>
      </div>

      {/* Compact activity feed */}
      {activities.length > 0 && (
        <div className="max-h-28 space-y-1 overflow-y-auto">
          {activities.map((a) => (
            <div key={a.id} className="flex gap-2 text-[10px]">
              <span className="shrink-0 text-gray-600">{a.time}</span>
              <span className="truncate text-gray-500">{a.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
