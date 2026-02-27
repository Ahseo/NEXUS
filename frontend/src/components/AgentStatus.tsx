"use client";

import { useEffect, useState } from "react";
import { agent } from "@/lib/api";

interface AgentStatusData {
  status: string;
  events_processed?: number;
  messages_sent?: number;
  uptime?: string;
}

export default function AgentStatus() {
  const [data, setData] = useState<AgentStatusData | null>(null);

  useEffect(() => {
    agent.status().then((d) => setData(d as AgentStatusData)).catch(() => {});
  }, []);

  const isRunning = data?.status === "running";

  return (
    <div className="flex items-center gap-2">
      <span
        className={`inline-block h-2.5 w-2.5 rounded-full ${
          isRunning ? "bg-green-500 animate-pulse" : "bg-yellow-500"
        }`}
      />
      <span className="text-sm text-gray-400">
        Agent {isRunning ? "Running" : data?.status ?? "Unknown"}
      </span>
    </div>
  );
}
