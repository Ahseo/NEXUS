"use client";

import { useEffect, useState, use } from "react";
import { events as eventsApi } from "@/lib/api";
import type { Event, Person } from "@/lib/types";
import PersonCard from "@/components/PersonCard";

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-green-900 text-green-300"
      : score >= 50
        ? "bg-yellow-900 text-yellow-300"
        : "bg-red-900 text-red-300";
  return (
    <span className={`rounded-full px-3 py-1 text-sm font-medium ${color}`}>
      {score}
    </span>
  );
}

const statusColors: Record<string, string> = {
  discovered: "bg-gray-700 text-gray-300",
  analyzed: "bg-blue-900 text-blue-300",
  suggested: "bg-indigo-900 text-indigo-300",
  accepted: "bg-yellow-900 text-yellow-300",
  applied: "bg-green-900 text-green-300",
  confirmed: "bg-green-800 text-green-200",
  rejected: "bg-red-900 text-red-300",
  waitlisted: "bg-orange-900 text-orange-300",
  attended: "bg-emerald-900 text-emerald-300",
  skipped: "bg-gray-800 text-gray-400",
};

export default function EventDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [event, setEvent] = useState<Event | null>(null);
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      eventsApi.get(id).catch(() => null),
      eventsApi.people(id).catch(() => []),
    ]).then(([ev, ppl]) => {
      setEvent(ev as Event | null);
      setPeople(ppl as Person[]);
      setLoading(false);
    });
  }, [id]);

  const handleAccept = async () => {
    if (!event) return;
    try {
      await eventsApi.accept(event.id);
      setEvent({ ...event, status: "accepted" });
    } catch {
      /* ignore */
    }
  };

  const handleReject = async () => {
    if (!event) return;
    try {
      await eventsApi.reject(event.id, "rejected by user");
      setEvent({ ...event, status: "rejected" });
    } catch {
      /* ignore */
    }
  };

  const handleApply = async () => {
    if (!event) return;
    try {
      await eventsApi.apply(event.id);
      setEvent({ ...event, status: "applied" });
    } catch {
      /* ignore */
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-gray-500">
        Loading event...
      </div>
    );
  }

  if (!event) {
    return (
      <div className="flex h-full items-center justify-center text-gray-500">
        Event not found.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      {/* Event Header */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-3">
          <ScoreBadge score={event.relevance_score} />
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              statusColors[event.status] ?? "bg-gray-700 text-gray-300"
            }`}
          >
            {event.status}
          </span>
          <span className="text-xs uppercase text-gray-500">{event.source}</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-100">{event.title}</h1>
      </div>

      {/* Event Details */}
      <div className="mb-6 grid grid-cols-2 gap-4 rounded-lg border border-gray-800 bg-gray-900 p-4">
        <div>
          <p className="text-xs text-gray-500">Date</p>
          <p className="text-sm text-gray-200">
            {new Date(event.date).toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Location</p>
          <p className="text-sm text-gray-200">{event.location}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Type</p>
          <p className="text-sm capitalize text-gray-200">{event.event_type}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Price</p>
          <p className="text-sm text-gray-200">
            {event.price != null && event.price > 0
              ? `$${event.price}`
              : "Free"}
          </p>
        </div>
        {event.capacity && (
          <div>
            <p className="text-xs text-gray-500">Capacity</p>
            <p className="text-sm text-gray-200">{event.capacity}</p>
          </div>
        )}
        <div>
          <p className="text-xs text-gray-500">Source</p>
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-indigo-400 hover:text-indigo-300"
          >
            View original
          </a>
        </div>
      </div>

      {/* Topics */}
      {event.topics.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-semibold text-gray-400">Topics</h2>
          <div className="flex flex-wrap gap-2">
            {event.topics.map((t) => (
              <span
                key={t}
                className="rounded-full bg-gray-800 px-3 py-1 text-xs text-gray-300"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mb-8 flex items-center gap-3">
        <button
          onClick={handleAccept}
          disabled={event.status !== "suggested" && event.status !== "analyzed" && event.status !== "discovered"}
          className="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Accept
        </button>
        <button
          onClick={handleReject}
          disabled={event.status === "rejected" || event.status === "skipped"}
          className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Reject
        </button>
        <button
          onClick={handleApply}
          disabled={event.status !== "accepted"}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Apply Manually
        </button>
      </div>

      {/* People Section */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-200">
          People You Should Meet
        </h2>
        {people.length === 0 ? (
          <p className="text-sm text-gray-600">
            No people discovered for this event yet.
          </p>
        ) : (
          <div className="space-y-3">
            {people.map((person) => (
              <PersonCard
                key={person.id}
                person={person}
                reason={person.research_summary}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
