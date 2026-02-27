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
  const isHigh = score >= 80;
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums transition-colors ${
        isHigh
          ? "bg-orange-50 text-orange-600"
          : score >= 50
            ? "bg-gray-100 text-gray-600"
            : "bg-gray-50 text-gray-400"
      }`}
    >
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
    <div className="group rounded-2xl border border-black/[0.04] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex items-center gap-2">
            <span className="rounded-md bg-gray-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gray-400">
              {sourceIcons[event.source] ?? "OT"}
            </span>
            <ScoreBadge score={event.relevance_score} />
            {event.application_result?.status === "applied" && (
              <span className="rounded-full bg-[#1a1a1a] px-2 py-0.5 text-[10px] font-semibold text-white">
                Applied
              </span>
            )}
            {event.application_result?.status === "payment_required" && (
              <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-semibold text-orange-600">
                Payment Required
              </span>
            )}
            {event.application_result?.status === "waitlisted" && (
              <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-[10px] font-semibold text-yellow-700">
                Waitlisted
              </span>
            )}
            <span className="truncate text-[12px] text-gray-400">
              {event.event_type}
            </span>
          </div>
          <Link
            href={`/events/${event.id}`}
            className="text-[15px] font-semibold text-gray-900 transition-colors duration-200 hover:text-gray-600"
          >
            {event.title}
          </Link>
          <div className="mt-1.5 flex flex-wrap items-center gap-3 text-[12px] text-gray-400">
            <span>{new Date(event.date).toLocaleDateString("en-US", { month: "short", day: "numeric", weekday: "short" })}</span>
            <span>{event.location}</span>
            {event.price != null && event.price > 0 && (
              <span className="font-medium text-gray-500">${event.price}</span>
            )}
          </div>
        </div>
      </div>
      {(onAccept || onSkip) && (
        <div className="mt-3 flex items-center gap-2 pt-2 border-t border-black/[0.04]">
          {onAccept && (
            <button
              onClick={() => onAccept(event.id)}
              className="rounded-lg bg-[#1a1a1a] px-3.5 py-1.5 text-[12px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]"
            >
              Accept & Apply
            </button>
          )}
          {onSkip && (
            <button
              onClick={() => onSkip(event.id)}
              className="rounded-lg border border-black/[0.06] bg-white px-3.5 py-1.5 text-[12px] font-medium text-gray-500 transition-all duration-200 hover:bg-gray-50 hover:text-gray-700 active:scale-[0.97]"
            >
              Skip
            </button>
          )}
          <Link
            href={`/events/${event.id}`}
            className="ml-auto text-[12px] text-gray-400 transition-colors duration-200 hover:text-gray-700"
          >
            Details &rarr;
          </Link>
        </div>
      )}
    </div>
  );
}
