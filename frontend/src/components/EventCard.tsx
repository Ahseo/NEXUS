"use client";

import Link from "next/link";
import type { Event } from "@/lib/types";

const sourceIcons: Record<string, string> = {
  eventbrite: "EB",
  luma: "LU",
  meetup: "MU",
  partiful: "PA",
  twitter: "TW",
  other: "OT",
};

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-green-900 text-green-300"
      : score >= 50
        ? "bg-yellow-900 text-yellow-300"
        : "bg-red-900 text-red-300";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {score}
    </span>
  );
}

export default function EventCard({
  event,
  onAccept,
  onSkip,
}: {
  event: Event;
  onAccept?: (id: string) => void;
  onSkip?: (id: string) => void;
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4 transition hover:border-gray-700">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gray-400">
              {sourceIcons[event.source] ?? "OT"}
            </span>
            <ScoreBadge score={event.relevance_score} />
            <span className="truncate text-sm text-gray-500">
              {event.event_type}
            </span>
          </div>
          <Link
            href={`/events/${event.id}`}
            className="text-base font-semibold text-gray-100 hover:text-indigo-400"
          >
            {event.title}
          </Link>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span>{new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", weekday: "short" })}</span>
            <span>{event.location}</span>
            {event.price != null && event.price > 0 && (
              <span>${event.price}</span>
            )}
          </div>
        </div>
      </div>
      {(onAccept || onSkip) && (
        <div className="mt-3 flex items-center gap-2">
          {onAccept && (
            <button
              onClick={() => onAccept(event.id)}
              className="rounded bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-500"
            >
              Accept & Apply
            </button>
          )}
          {onSkip && (
            <button
              onClick={() => onSkip(event.id)}
              className="rounded bg-gray-700 px-3 py-1 text-xs font-medium text-gray-300 hover:bg-gray-600"
            >
              Skip
            </button>
          )}
          <Link
            href={`/events/${event.id}`}
            className="ml-auto text-xs text-indigo-400 hover:text-indigo-300"
          >
            Details
          </Link>
        </div>
      )}
    </div>
  );
}
