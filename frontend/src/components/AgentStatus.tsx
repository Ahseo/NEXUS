"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthProvider";
import { agent } from "@/lib/api";

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

  // Fetch real agent status on mount (so refresh doesn't show stale "idle")
  useEffect(() => {
    agent.status().then((raw: unknown) => {
      const data = raw as Record<string, unknown>;
      if (typeof data.status === "string") {
        setStatus(data.status);
      }
    }).catch(() => { /* ignore */ });
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

          const source = (data.agent as string) || "wingman";
          if (source === "chat") return;

          if (type === "agent:status") {
            const newStatus = data.status as string;
            setStatus(newStatus);
            // Dispatch custom event so other components (e.g. dashboard) can react
            window.dispatchEvent(new CustomEvent("agent:status", { detail: newStatus }));
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
            ...prev.slice(0, 9),
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2 w-2 rounded-full transition-all duration-300 ${
              !connected
                ? "bg-gray-300"
                : status === "running"
                  ? "bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.4)] animate-pulse"
                  : "bg-gray-400"
            }`}
          />
          <span className="text-[11px] text-gray-500">
            {!connected ? "Offline" : `Agent ${status}`}
          </span>
        </div>
        <Link
          href="/activity"
          className="text-[10px] text-gray-400 transition-colors duration-200 hover:text-gray-700"
          title="View full activity log"
        >
          View all
        </Link>
      </div>

      {activities.length > 0 && (
        <div className="max-h-24 space-y-0.5 overflow-y-auto">
          {activities.map((a) => (
            <div key={a.id} className="flex gap-2 text-[10px] animate-fade-in-up">
              <span className="shrink-0 text-gray-400">{a.time}</span>
              <span className="truncate text-gray-500">{a.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
