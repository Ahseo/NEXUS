"use client";

import { useEffect, useState } from "react";
import { events as eventsApi, agent } from "@/lib/api";
import type { Event } from "@/lib/types";
import EventCard from "@/components/EventCard";

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
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
          <p className="text-sm text-gray-500">Your networking activity at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              agentData?.status === "running" ? "bg-green-500 animate-pulse" : "bg-yellow-500"
            }`}
          />
          <span className="text-sm text-gray-400">
            Agent {agentData?.status ?? "..."}
          </span>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="mb-8 grid grid-cols-3 gap-4">
        {[
          { label: "Events Discovered", value: weekEvents },
          { label: "Applied", value: appliedCount },
          { label: "Connections Made", value: connectionsCount },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-gray-800 bg-gray-900 p-4"
          >
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className="mt-1 text-2xl font-bold text-gray-100">
              {loading ? "--" : stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Event Sections */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-gray-500">
          Loading events...
        </div>
      ) : (
        <div className="space-y-8">
          {/* New Events */}
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-500">
              <span className="inline-block h-2 w-2 rounded-full bg-indigo-500" />
              New ({newEvents.length})
            </h2>
            {newEvents.length === 0 ? (
              <p className="text-sm text-gray-600">No new events right now.</p>
            ) : (
              <div className="space-y-3">
                {newEvents.map((event) => (
                  <EventCard
                    key={event.id}
                    event={event}
                    onAccept={handleAccept}
                    onSkip={handleSkip}
                  />
                ))}
              </div>
            )}
          </section>

          {/* Auto-Applied */}
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-500">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              Auto-Applied ({appliedEvents.length})
            </h2>
            {appliedEvents.length === 0 ? (
              <p className="text-sm text-gray-600">No auto-applied events yet.</p>
            ) : (
              <div className="space-y-3">
                {appliedEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            )}
          </section>

          {/* Pending Review */}
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-500">
              <span className="inline-block h-2 w-2 rounded-full bg-yellow-500" />
              Pending Review ({pendingEvents.length})
            </h2>
            {pendingEvents.length === 0 ? (
              <p className="text-sm text-gray-600">No events pending review.</p>
            ) : (
              <div className="space-y-3">
                {pendingEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
