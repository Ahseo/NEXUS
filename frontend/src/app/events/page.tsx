"use client";

import { useEffect, useState } from "react";
import { agent } from "@/lib/api";

interface EventEntry {
  id: string;
  title: string;
  url: string;
  status: "discovered" | "applied" | "scheduled";
  score?: string;
  detail: string;
  time: string;
  eventDate?: string;
  data: Record<string, unknown> | null;
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "discovered" | "applied" | "scheduled">("all");
  const [selected, setSelected] = useState<EventEntry | null>(null);

  useEffect(() => {
    agent
      .events({ limit: 500 })
      .then((data) => {
        const eventTypes = ["event:discovered", "event:applied", "event:scheduled"];
        const parsed: EventEntry[] = data
          .filter((e) => eventTypes.includes(e.type))
          .map((e) => {
            const status = e.type.split(":")[1] as EventEntry["status"];
            let title = e.message;
            title = title
              .replace(/^Found event:\s*/, "")
              .replace(/^Applied to:\s*/, "")
              .replace(/^Scheduled:\s*/, "");

            let url = "";
            const d = e.data as Record<string, unknown> | null;
            if (d) {
              const ev = d.event as Record<string, string> | undefined;
              if (ev?.url) url = ev.url;
            }
            if (!url && e.detail && e.detail.startsWith("http")) {
              url = e.detail;
            }

            // Extract event date from data
            let eventDate: string | undefined;
            if (d) {
              const ev = d.event as Record<string, string> | undefined;
              if (ev?.date) eventDate = ev.date;
              if (ev?.start_date) eventDate = ev.start_date;
              if (!eventDate && typeof d.date === "string") eventDate = d.date;
            }

            return {
              id: e.id,
              title,
              url,
              status,
              score: e.detail?.replace("Count: ", "").replace("Score: ", ""),
              detail: e.detail,
              time: e.time ? new Date(e.time).toLocaleString() : "",
              eventDate,
              data: d,
            };
          });
        setEvents(parsed);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filtered = events.filter((e) => {
    if (filter === "all") return true;
    return e.status === filter;
  });

  const discoveredCount = events.filter((e) => e.status === "discovered").length;
  const appliedCount = events.filter((e) => e.status === "applied").length;
  const scheduledCount = events.filter((e) => e.status === "scheduled").length;

  return (
    <div className="flex h-full flex-col animate-fade-in">
      {/* Header */}
      <div className="border-b border-black/[0.04] px-6 py-5">
        <h1 className="text-xl font-bold text-gray-900">Events</h1>
        <p className="text-[12px] text-gray-400">Discovered and applied by your agent</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 border-b border-black/[0.04] px-6 py-4 stagger-children">
        {[
          { label: "Discovered", value: discoveredCount },
          { label: "Applied", value: appliedCount },
          { label: "Scheduled", value: scheduledCount },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-2xl border border-black/[0.04] bg-white p-4 text-center shadow-[0_1px_3px_rgba(0,0,0,0.03)] transition-all duration-300 hover:shadow-md hover:-translate-y-0.5"
          >
            <p className="text-2xl font-bold text-gray-900 tabular-nums">{s.value}</p>
            <p className="text-[11px] text-gray-400 font-medium">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1.5 border-b border-black/[0.04] px-6 py-3">
        {(["all", "discovered", "applied", "scheduled"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3.5 py-1.5 text-[12px] font-medium capitalize transition-all duration-200 ${
              filter === f
                ? "bg-[#1a1a1a] text-white shadow-sm"
                : "text-gray-400 hover:bg-black/[0.04] hover:text-gray-600"
            }`}
          >
            {f === "all" ? `All (${events.length})` : `${f} (${events.filter((e) => e.status === f).length})`}
          </button>
        ))}
      </div>

      {/* Event list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="space-y-3 p-6">
            {[1, 2, 3, 4].map((n) => (
              <div
                key={n}
                className="h-20 rounded-2xl bg-white/60 animate-pulse"
                style={{ animationDelay: `${n * 80}ms` }}
              />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex h-40 flex-col items-center justify-center text-center animate-fade-in">
            <p className="text-sm text-gray-400">No events yet</p>
            <p className="mt-1 text-[12px] text-gray-300">
              Events will appear here as the agent discovers them
            </p>
          </div>
        ) : (
          <div className="space-y-2 p-4 stagger-children">
            {filtered.map((ev) => (
              <button
                key={ev.id}
                onClick={() => setSelected(ev)}
                className="group flex w-full items-center gap-4 rounded-2xl border border-black/[0.04] bg-white px-5 py-4 text-left shadow-[0_1px_2px_rgba(0,0,0,0.03)] transition-all duration-300 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:-translate-y-0.5"
              >
                {/* Status */}
                <span
                  className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${
                    ev.status === "applied"
                      ? "bg-[#1a1a1a] text-white"
                      : ev.status === "scheduled"
                        ? "bg-gray-200 text-gray-600"
                        : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {ev.status}
                </span>

                {/* Info */}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[14px] font-medium text-gray-900 transition-colors group-hover:text-gray-600">
                    {ev.title}
                  </p>
                  <div className="mt-1 flex items-center gap-3">
                    {ev.eventDate && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-orange-600">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(ev.eventDate).toLocaleDateString("en-US", { month: "short", day: "numeric", weekday: "short" })}
                      </span>
                    )}
                    {ev.detail && (
                      <span className="truncate text-[11px] text-gray-400">{ev.detail}</span>
                    )}
                  </div>
                </div>

                {/* URL indicator */}
                {ev.url && (
                  <span className="shrink-0 text-[10px] text-gray-300">
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </span>
                )}

                {/* Time */}
                <span className="shrink-0 font-mono text-[11px] text-gray-300">
                  {ev.time}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selected && (
        <EventModal event={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function EventModal({ event, onClose }: { event: EventEntry; onClose: () => void }) {
  const d = event.data ?? {};
  const ev = (d.event ?? {}) as Record<string, unknown>;
  const eventTitle = (ev.title as string) || event.title;
  const eventUrl = (ev.url as string) || event.url;
  const eventStatus = (d.status as string) || event.status;
  const eventDate = (ev.date as string) || (ev.start_date as string) || event.eventDate;
  const count = d.count as number | undefined;
  const score = d.score as number | undefined;
  const results = (d.results ?? d.search_results ?? []) as Record<string, unknown>[];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative mx-4 max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-black/[0.06] bg-white/95 p-6 shadow-2xl backdrop-blur-xl animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-gray-400 transition-all duration-200 hover:bg-gray-100 hover:text-gray-600"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Status + Time */}
        <div className="mb-4 flex items-center gap-2">
          <span className="rounded-full bg-[#1a1a1a] px-2.5 py-1 text-[10px] font-semibold capitalize text-white">
            {event.status}
          </span>
          <span className="text-[11px] text-gray-400">{event.time}</span>
        </div>

        {/* Title */}
        <h2 className="mb-2 text-lg font-bold text-gray-900">{eventTitle}</h2>

        {/* Event Date */}
        {eventDate && (
          <div className="mb-3 flex items-center gap-2 rounded-xl bg-orange-50 px-3 py-2 text-[13px] font-medium text-orange-600">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {new Date(eventDate).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
          </div>
        )}

        {/* Link */}
        {eventUrl && (
          <a
            href={eventUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mb-4 flex items-center gap-2 truncate text-[13px] text-gray-500 transition-colors hover:text-[#1a1a1a]"
          >
            <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
            {eventUrl}
          </a>
        )}

        {/* Meta */}
        <div className="mb-4 space-y-2">
          {event.detail && (
            <div className="rounded-xl bg-[#F7F7F4] p-3">
              <p className="text-[11px] font-medium text-gray-400">Detail</p>
              <p className="text-[13px] text-gray-700">{event.detail}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            {count != null && (
              <div className="rounded-xl bg-[#F7F7F4] p-3">
                <p className="text-[11px] font-medium text-gray-400">Results</p>
                <p className="text-lg font-bold text-gray-900">{count}</p>
              </div>
            )}
            {score != null && (
              <div className="rounded-xl bg-[#F7F7F4] p-3">
                <p className="text-[11px] font-medium text-gray-400">Score</p>
                <p className="text-lg font-bold text-gray-900">{score}</p>
              </div>
            )}
          </div>
          {eventStatus && eventStatus !== event.status && (
            <div className="rounded-xl bg-[#F7F7F4] p-3">
              <p className="text-[11px] font-medium text-gray-400">Apply Status</p>
              <p className="text-[13px] text-gray-700">{eventStatus}</p>
            </div>
          )}
        </div>

        {/* Search Results */}
        {results.length > 0 && (
          <div className="mb-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
              Search Results ({results.length})
            </p>
            <div className="space-y-2 stagger-children">
              {results.map((r, i) => (
                <div key={i} className="rounded-xl border border-black/[0.04] bg-[#F7F7F4] p-3">
                  <p className="text-[13px] font-medium text-gray-900">
                    {(r.title as string) || "Untitled"}
                  </p>
                  {typeof r.url === "string" && r.url && (
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-0.5 block truncate text-[11px] text-gray-400 transition-colors hover:text-gray-600"
                    >
                      {r.url}
                    </a>
                  )}
                  {typeof r.content === "string" && r.content && (
                    <p className="mt-1 text-[12px] text-gray-500 line-clamp-3">
                      {r.content}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Raw Data */}
        {event.data && Object.keys(event.data).length > 0 && (
          <details className="mt-4">
            <summary className="cursor-pointer text-[11px] text-gray-400 transition-colors hover:text-gray-600">
              Raw Data
            </summary>
            <pre className="mt-2 max-h-48 overflow-auto rounded-xl bg-[#F7F7F4] p-3 text-[11px] text-gray-500">
              {JSON.stringify(event.data, null, 2)}
            </pre>
          </details>
        )}

        {/* Actions */}
        <div className="mt-6 flex gap-2">
          {eventUrl && (
            <a
              href={eventUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl bg-[#1a1a1a] px-5 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]"
            >
              Open Event
            </a>
          )}
          <button
            onClick={onClose}
            className="rounded-xl border border-black/[0.06] px-5 py-2.5 text-[13px] font-medium text-gray-500 transition-all duration-200 hover:bg-gray-50 active:scale-[0.97]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
