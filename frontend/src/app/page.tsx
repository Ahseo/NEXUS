"use client";

import { useEffect, useState } from "react";
import { events as eventsApi, agent } from "@/lib/api";
import type { Event } from "@/lib/types";
import EventCard from "@/components/EventCard";
// import AgentWorkspace from "@/components/AgentWorkspace";

interface AgentStatusData {
  status: string;
  events_processed?: number;
  messages_sent?: number;
}

export default function DashboardPage() {
  const [eventList, setEventList] = useState<Event[]>([]);
  const [agentData, setAgentData] = useState<AgentStatusData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      eventsApi.list().catch(() => []),
      agent.status().catch(() => null),
    ]).then(([ev, ag]) => {
      setEventList(ev as Event[]);
      setAgentData(ag as AgentStatusData | null);
      setLoading(false);
    });
  }, []);

  // Listen for real-time agent status changes from WebSocket
  useEffect(() => {
    const handler = ((e: CustomEvent) => {
      const newStatus = e.detail as string;
      setAgentData((prev) => prev ? { ...prev, status: newStatus } : { status: newStatus });
    }) as EventListener;
    window.addEventListener("agent:status", handler);
    return () => window.removeEventListener("agent:status", handler);
  }, []);

  const handleAccept = async (id: string) => {
    try {
      await eventsApi.accept(id);
      setEventList((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: "accepted" } : e))
      );
    } catch {
      /* ignore */
    }
  };

  const handleSkip = async (id: string) => {
    try {
      await eventsApi.reject(id, "skipped");
      setEventList((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: "skipped" } : e))
      );
    } catch {
      /* ignore */
    }
  };

  const newEvents = eventList.filter(
    (e) => e.status === "discovered" || e.status === "analyzed" || e.status === "suggested"
  );
  const appliedEvents = eventList.filter(
    (e) => e.status === "applied" || e.status === "confirmed" || e.status === "waitlisted"
  );
  const pendingEvents = eventList.filter(
    (e) => e.status === "accepted"
  );

  const weekEvents = eventList.length;
  const appliedCount = appliedEvents.length;
  const connectionsCount = agentData?.messages_sent ?? 0;

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-[13px] text-gray-400">Your networking at a glance</p>
        </div>
        <div className="flex items-center gap-2.5 rounded-full border border-black/[0.04] bg-white px-3.5 py-2 shadow-sm">
          <span
            className={`inline-block h-2 w-2 rounded-full transition-all duration-500 ${
              agentData?.status === "running"
                ? "bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.4)] animate-pulse"
                : "bg-gray-300"
            }`}
          />
          <span className="text-[12px] font-medium text-gray-500">
            {agentData?.status ?? "loading"}
          </span>
        </div>
      </div>

      {/* Agent Workspace — commented out for now */}
      {/* <div className="mb-8">
        <AgentWorkspace />
      </div> */}

      {/* Stats */}
      <div className="mb-8 grid grid-cols-3 gap-4 stagger-children">
        {[
          { label: "Discovered", value: weekEvents, icon: "🔍" },
          { label: "Applied", value: appliedCount, icon: "✓" },
          { label: "Connections", value: connectionsCount, icon: "🤝" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="group rounded-2xl border border-black/[0.04] bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:-translate-y-0.5"
          >
            <p className="text-[12px] font-medium text-gray-400">{stat.label}</p>
            <p className="mt-2 text-3xl font-bold text-gray-900 tabular-nums">
              {loading ? (
                <span className="inline-block h-8 w-12 rounded-lg bg-gray-100 animate-pulse" />
              ) : (
                stat.value
              )}
            </p>
          </div>
        ))}
      </div>

      {/* Event Sections */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-24 rounded-2xl bg-white/60 animate-pulse"
              style={{ animationDelay: `${n * 100}ms` }}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          <EventSection
            title="New"
            count={newEvents.length}
            dotColor="bg-[#1a1a1a]"
            events={newEvents}
            onAccept={handleAccept}
            onSkip={handleSkip}
          />
          <EventSection
            title="Auto-Applied"
            count={appliedEvents.length}
            dotColor="bg-gray-400"
            events={appliedEvents}
          />
          <EventSection
            title="Pending"
            count={pendingEvents.length}
            dotColor="bg-gray-300"
            events={pendingEvents}
          />
        </div>
      )}
    </div>
  );
}

function EventSection({
  title,
  count,
  dotColor,
  events,
  onAccept,
  onSkip,
}: {
  title: string;
  count: number;
  dotColor: string;
  events: Event[];
  onAccept?: (id: string) => void;
  onSkip?: (id: string) => void;
}) {
  return (
    <section className="animate-fade-in-up">
      <h2 className="mb-3 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wider text-gray-400">
        <span className={`inline-block h-2 w-2 rounded-full ${dotColor}`} />
        {title} ({count})
      </h2>
      {events.length === 0 ? (
        <p className="text-[13px] text-gray-400">Nothing here yet.</p>
      ) : (
        <div className="space-y-3 stagger-children">
          {events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              onAccept={onAccept}
              onSkip={onSkip}
            />
          ))}
        </div>
      )}
    </section>
  );
}
