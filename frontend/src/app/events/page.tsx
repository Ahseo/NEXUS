"use client";

import { useEffect, useState } from "react";
import { agent } from "@/lib/api";

interface EventEntry {
  id: string;
  title: string;
  url: string;
  status: "discovered" | "applied" | "scheduled" | "analyzed";
  score?: string;
  detail: string;
  time: string;
  eventDate?: string;
  location?: string;
  description?: string;
  source?: string;
  price?: number | null;
  topics?: string[];
  speakers?: string[];
  paymentRequired?: boolean;
  paymentAmount?: number | null;
  applicationStatus?: string;
  why?: string;
  data: Record<string, unknown> | null;
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "discovered" | "applied" | "scheduled" | "analyzed">("all");
  const [selected, setSelected] = useState<EventEntry | null>(null);

  useEffect(() => {
    agent
      .events({ limit: 500 })
      .then((data) => {
        const eventTypes = ["event:discovered", "event:applied", "event:scheduled", "event:analyzed"];
        const parsed: EventEntry[] = [];

        for (const e of data) {
          if (!eventTypes.includes(e.type)) continue;

          const status = e.type.split(":")[1] as EventEntry["status"];
          const d = e.data as Record<string, unknown> | null;
          const time = e.time ? new Date(e.time).toLocaleString() : "";

          // For discovered events, flatten search results into individual entries
          if (status === "discovered" && d) {
            const rawResults = (d.search_results ?? d.results ?? []) as Record<string, unknown>[];
            if (Array.isArray(rawResults) && rawResults.length > 0) {
              for (let i = 0; i < rawResults.length; i++) {
                const r = rawResults[i];
                parsed.push({
                  id: `${e.id}-r${i}`,
                  title: (r.title as string) || "Untitled",
                  url: (r.url as string) || "",
                  status: "discovered",
                  detail: "",
                  time,
                  description: (r.content as string) || undefined,
                  data: d,
                });
              }
              continue; // skip the parent "discovered" entry
            }
          }

          // Non-discovered or discovered without results — parse normally
          let title = e.message;
          title = title
            .replace(/^Found event:\s*/, "")
            .replace(/^Applied to:\s*/, "")
            .replace(/^Scheduled:\s*/, "")
            .replace(/^Recommended:\s*/, "")
            .replace(/^Payment required:\s*/, "")
            .replace(/\s*\(Score:.*\)$/, "");

          let url = "";
          if (d) {
            const ev = d.event as Record<string, string> | undefined;
            if (ev?.url) url = ev.url;
          }
          if (!url && e.detail && e.detail.startsWith("http")) {
            url = e.detail;
          }

          let eventDate: string | undefined;
          let location: string | undefined;
          let description: string | undefined;
          let source: string | undefined;
          let price: number | null | undefined;
          let topics: string[] | undefined;
          let speakers: string[] | undefined;
          let paymentRequired: boolean | undefined;
          let paymentAmount: number | null | undefined;
          let applicationStatus: string | undefined;
          let why: string | undefined;

          if (d) {
            const ev = d.event as Record<string, unknown> | undefined;
            if (ev?.date) eventDate = ev.date as string;
            if (ev?.start_date) eventDate = ev.start_date as string;
            if (!eventDate && typeof d.date === "string") eventDate = d.date;
            if (ev?.location) location = ev.location as string;
            if (ev?.description) description = ev.description as string;
            if (ev?.source) source = ev.source as string;
            if (ev?.price !== undefined) price = ev.price as number | null;
            if (Array.isArray(ev?.topics)) topics = ev.topics as string[];
            if (Array.isArray(ev?.speakers)) speakers = ev.speakers as string[];
            if (d.payment_required !== undefined) paymentRequired = d.payment_required as boolean;
            if (d.payment_amount !== undefined) paymentAmount = d.payment_amount as number | null;
            if (typeof d.application_status === "string") applicationStatus = d.application_status;
            if (typeof d.why === "string") why = d.why;
          }

          parsed.push({
            id: e.id,
            title,
            url,
            status,
            score: d?.score != null ? String(d.score) : e.detail?.replace("Count: ", "").replace("Score: ", ""),
            detail: e.detail,
            time,
            eventDate,
            location,
            description,
            source,
            price,
            topics,
            speakers,
            paymentRequired,
            paymentAmount,
            applicationStatus,
            why,
            data: d,
          });
        }
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
  const analyzedCount = events.filter((e) => e.status === "analyzed").length;
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
      <div className="grid grid-cols-4 gap-4 border-b border-black/[0.04] px-6 py-4 stagger-children">
        {[
          { label: "Discovered", value: discoveredCount },
          { label: "Recommended", value: analyzedCount },
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
        {(["all", "discovered", "analyzed", "applied", "scheduled"] as const).map((f) => {
          const label = f === "analyzed" ? "Recommended" : f;
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full px-3.5 py-1.5 text-[12px] font-medium capitalize transition-all duration-200 ${
                filter === f
                  ? "bg-[#1a1a1a] text-white shadow-sm"
                  : "text-gray-400 hover:bg-black/[0.04] hover:text-gray-600"
              }`}
            >
              {f === "all" ? `All (${events.length})` : `${label} (${events.filter((e) => e.status === f).length})`}
            </button>
          );
        })}
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
                {/* Status badge */}
                <span
                  className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${
                    ev.paymentRequired
                      ? "bg-orange-100 text-orange-600"
                      : ev.status === "applied"
                        ? "bg-[#1a1a1a] text-white"
                        : ev.status === "analyzed"
                          ? "bg-blue-50 text-blue-600"
                          : ev.status === "scheduled"
                            ? "bg-gray-200 text-gray-600"
                            : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {ev.paymentRequired ? "Payment" : ev.status === "analyzed" ? "Recommended" : ev.status}
                </span>

                {/* Info */}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[14px] font-medium text-gray-900 transition-colors group-hover:text-gray-600">
                    {ev.title}
                  </p>
                  {ev.why && (
                    <p className="mt-0.5 truncate text-[12px] italic text-gray-400">
                      {ev.why}
                    </p>
                  )}
                  <div className="mt-1 flex items-center gap-3">
                    {ev.eventDate && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-orange-600">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(ev.eventDate).toLocaleDateString("en-US", { month: "short", day: "numeric", weekday: "short" })}
                      </span>
                    )}
                    {ev.location && (
                      <span className="text-[11px] text-gray-400">{ev.location}</span>
                    )}
                    {ev.price != null && (
                      <span className={`text-[11px] font-medium ${ev.price === 0 ? "text-green-600" : "text-gray-500"}`}>
                        {ev.price === 0 ? "Free" : `$${ev.price}`}
                      </span>
                    )}
                    {ev.score && (
                      <span className="text-[11px] font-medium text-blue-500">Score: {ev.score}</span>
                    )}
                  </div>
                </div>

                {/* Payment badge */}
                {ev.paymentRequired && (
                  <span className="shrink-0 rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-semibold text-orange-600">
                    ${ev.paymentAmount ?? "?"}
                  </span>
                )}

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
          <span
            className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${
              event.paymentRequired
                ? "bg-orange-100 text-orange-600"
                : event.status === "applied"
                  ? "bg-[#1a1a1a] text-white"
                  : event.status === "analyzed"
                    ? "bg-blue-50 text-blue-600"
                    : "bg-gray-100 text-gray-500"
            }`}
          >
            {event.paymentRequired ? "Payment Required" : event.status === "analyzed" ? "Recommended" : event.status}
          </span>
          <span className="text-[11px] text-gray-400">{event.time}</span>
        </div>

        {/* Payment Required Warning */}
        {event.paymentRequired && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-orange-50 border border-orange-200 px-4 py-3">
            <svg className="h-5 w-5 shrink-0 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="text-[13px] font-semibold text-orange-700">Payment Required</p>
              <p className="text-[12px] text-orange-600">
                This event requires payment{event.paymentAmount ? ` — $${event.paymentAmount}` : ""}. Registration was paused.
              </p>
            </div>
          </div>
        )}

        {/* Title */}
        <h2 className="mb-2 text-lg font-bold text-gray-900">{eventTitle}</h2>

        {/* Why Recommended */}
        {event.why && (
          <div className="mb-3 rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
            <p className="text-[11px] font-semibold text-blue-500 mb-1">Why Recommended</p>
            <p className="text-[13px] text-blue-700">{event.why}</p>
          </div>
        )}

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

        {/* Description */}
        {event.description && (
          <div className="mb-4 rounded-xl bg-[#F7F7F4] p-3">
            <p className="text-[11px] font-medium text-gray-400">Description</p>
            <p className="mt-1 text-[13px] text-gray-700">{event.description}</p>
          </div>
        )}

        {/* Meta */}
        <div className="mb-4 space-y-2">
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
            {event.location && (
              <div className="rounded-xl bg-[#F7F7F4] p-3">
                <p className="text-[11px] font-medium text-gray-400">Location</p>
                <p className="text-[13px] text-gray-700">{event.location}</p>
              </div>
            )}
            {event.price != null && (
              <div className="rounded-xl bg-[#F7F7F4] p-3">
                <p className="text-[11px] font-medium text-gray-400">Price</p>
                <p className={`text-lg font-bold ${event.price === 0 ? "text-green-600" : "text-gray-900"}`}>
                  {event.price === 0 ? "Free" : `$${event.price}`}
                </p>
              </div>
            )}
          </div>

          {/* Application Status */}
          {event.applicationStatus && (
            <div className="rounded-xl bg-[#F7F7F4] p-3">
              <p className="text-[11px] font-medium text-gray-400">Application Status</p>
              <p className="text-[13px] font-medium capitalize text-gray-700">{event.applicationStatus}</p>
            </div>
          )}

          {eventStatus && eventStatus !== event.status && !event.applicationStatus && (
            <div className="rounded-xl bg-[#F7F7F4] p-3">
              <p className="text-[11px] font-medium text-gray-400">Apply Status</p>
              <p className="text-[13px] text-gray-700">{eventStatus}</p>
            </div>
          )}
        </div>

        {/* Topics */}
        {event.topics && event.topics.length > 0 && (
          <div className="mb-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Topics</p>
            <div className="flex flex-wrap gap-1.5">
              {event.topics.map((t, i) => (
                <span key={i} className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-600">
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Speakers */}
        {event.speakers && event.speakers.length > 0 && (
          <div className="mb-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Speakers</p>
            <div className="space-y-1">
              {event.speakers.map((s, i) => (
                <p key={i} className="text-[13px] text-gray-700">{s}</p>
              ))}
            </div>
          </div>
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
