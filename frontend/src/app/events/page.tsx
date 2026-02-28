"use client";

import { useEffect, useState } from "react";
import { agent, events as eventsApi } from "@/lib/api";

interface EventEntry {
  id: string;
  title: string;
  url: string;
  status: "discovered" | "applied" | "scheduled" | "analyzed" | "attended";
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

interface Connection {
  name: string;
  linkedin_url: string;
  notes: string;
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "discovered" | "applied" | "scheduled" | "analyzed" | "attended">("all");
  const [selected, setSelected] = useState<EventEntry | null>(null);
  const [attendModal, setAttendModal] = useState<EventEntry | null>(null);

  useEffect(() => {
    agent
      .events({ limit: 500 })
      .then((data) => {
        const eventTypes = ["event:discovered", "event:applied", "event:scheduled", "event:analyzed", "event:attended"];
        const parsed: EventEntry[] = [];

        for (const e of data) {
          if (!eventTypes.includes(e.type)) continue;

          const status = e.type.split(":")[1] as EventEntry["status"];
          const d = e.data as Record<string, unknown> | null;
          const time = e.time ? new Date(e.time).toLocaleString() : "";

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
              continue;
            }
          }

          let title = e.message;
          title = title
            .replace(/^Found event:\s*/, "")
            .replace(/^Applied to:\s*/, "")
            .replace(/^Scheduled:\s*/, "")
            .replace(/^Recommended:\s*/, "")
            .replace(/^Payment required:\s*/, "")
            .replace(/^Attended:\s*/, "")
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
            if (!location && typeof d.location === "string") location = d.location;
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
  const attendedCount = events.filter((e) => e.status === "attended").length;

  const handleAttend = (ev: EventEntry) => {
    setAttendModal(ev);
  };

  const handleSkipAttend = async (ev: EventEntry) => {
    try {
      await eventsApi.skipAttend(ev.id);
      setEvents((prev) => prev.filter((e) => e.id !== ev.id));
    } catch { /* ignore */ }
  };

  const handleAttendConfirmed = async (ev: EventEntry) => {
    try {
      await eventsApi.attend(ev.id);
      setEvents((prev) =>
        prev.map((e) => (e.id === ev.id ? { ...e, status: "attended" as const } : e))
      );
    } catch { /* ignore */ }
  };

  const isPastEvent = (ev: EventEntry) => {
    if (!ev.eventDate) return false;
    return new Date(ev.eventDate) < new Date();
  };

  return (
    <div className="flex h-full flex-col animate-fade-in">
      {/* Header */}
      <div className="border-b border-black/[0.04] px-6 py-5">
        <h1 className="text-xl font-bold text-gray-900">Events</h1>
        <p className="text-[12px] text-gray-400">Discovered and applied by your agent</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-3 border-b border-black/[0.04] px-6 py-4 stagger-children">
        {[
          { label: "Discovered", value: discoveredCount },
          { label: "Recommended", value: analyzedCount },
          { label: "Applied", value: appliedCount },
          { label: "Scheduled", value: scheduledCount },
          { label: "Attended", value: attendedCount },
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
        {(["all", "discovered", "analyzed", "applied", "scheduled", "attended"] as const).map((f) => {
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
              <div key={ev.id} className="group flex w-full items-center gap-4 rounded-2xl border border-black/[0.04] bg-white px-5 py-4 text-left shadow-[0_1px_2px_rgba(0,0,0,0.03)] transition-all duration-300 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:-translate-y-0.5">
                <button
                  onClick={() => setSelected(ev)}
                  className="flex min-w-0 flex-1 items-center gap-4"
                >
                  {/* Status badge + Score */}
                  <div className="flex shrink-0 items-center gap-2">
                    <span
                      className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${
                        ev.status === "attended"
                          ? "bg-green-100 text-green-700"
                          : ev.paymentRequired
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
                      {ev.status === "attended" ? "Attended" : ev.paymentRequired ? "Payment" : ev.status === "analyzed" ? "Recommended" : ev.status}
                    </span>
                    {ev.score && (
                      <span className="text-[10px] font-medium tabular-nums text-blue-500">Score {ev.score}</span>
                    )}
                  </div>

                  {/* Title */}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-medium text-gray-900 transition-colors group-hover:text-gray-600">
                      {ev.title}
                    </p>
                    {ev.why && (
                      <p className="mt-0.5 truncate text-[12px] italic text-gray-400">
                        {ev.why}
                      </p>
                    )}
                    {ev.applicationStatus && ev.applicationStatus !== "queued" && (
                      <span className="mt-1 inline-block rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-semibold capitalize text-gray-500">
                        {ev.applicationStatus}
                      </span>
                    )}
                  </div>

                  {/* Date / Location / Price */}
                  <div className="hidden shrink-0 items-center gap-3 sm:flex">
                    {ev.eventDate && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-orange-600">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(ev.eventDate).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                      </span>
                    )}
                    {ev.location && (
                      <span className="max-w-[140px] truncate text-[11px] text-gray-400">
                        {ev.location}
                      </span>
                    )}
                    {ev.price != null && (
                      <span className={`text-[11px] font-medium ${ev.price === 0 ? "text-green-600" : "text-gray-500"}`}>
                        {ev.price === 0 ? "Free" : `$${ev.price}`}
                      </span>
                    )}
                  </div>

                  {/* URL indicator */}
                  {ev.url && (
                    <span className="shrink-0 text-[10px] text-gray-300">
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                      </svg>
                    </span>
                  )}

                  <span className="shrink-0 font-mono text-[11px] text-gray-300">
                    {ev.time}
                  </span>
                </button>

                {/* Mark as Attended button for applied events */}
                {ev.status === "applied" && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleAttend(ev); }}
                    className="shrink-0 rounded-xl bg-green-600 px-3 py-1.5 text-[11px] font-semibold text-white transition-all hover:bg-green-700 active:scale-[0.97]"
                  >
                    Mark as Attended
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selected && (
        <EventModal
          event={selected}
          onClose={() => setSelected(null)}
          onAttend={selected.status === "applied" ? () => { setSelected(null); handleAttend(selected); } : undefined}
        />
      )}

      {/* Post-Attend Modal */}
      {attendModal && (
        <AttendModal
          event={attendModal}
          onClose={() => setAttendModal(null)}
          onSubmit={async (connections) => {
            await handleAttendConfirmed(attendModal);
            if (connections.length > 0) {
              try {
                await eventsApi.addConnections(attendModal.id, connections);
                await eventsApi.analyzeConnections(attendModal.id);
              } catch { /* ignore */ }
            }
            setAttendModal(null);
          }}
        />
      )}
    </div>
  );
}

/* ── Post-Attend Modal (Event Participants Multi-Select) ───────────────────── */

interface Participant {
  id: string;
  name: string;
  title: string;
  company: string;
  role: string;
  linkedin: string;
  avatar_color: string;
  connection_score: number;
  topics: string[];
}

function AttendModal({
  event,
  onClose,
  onSubmit,
}: {
  event: EventEntry;
  onClose: () => void;
  onSubmit: (connections: Connection[]) => Promise<void>;
}) {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showManual, setShowManual] = useState(false);
  const [manualRows, setManualRows] = useState<Connection[]>([{ name: "", linkedin_url: "", notes: "" }]);

  // Fetch participants from Neo4j on mount
  useEffect(() => {
    eventsApi.participants(event.id).then((p) => {
      setParticipants(p);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [event.id]);

  const toggleSelect = (i: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === participants.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(participants.map((_, i) => i)));
    }
  };

  const addManualRow = () => {
    setManualRows([...manualRows, { name: "", linkedin_url: "", notes: "" }]);
  };

  const updateManualRow = (i: number, field: keyof Connection, value: string) => {
    setManualRows(manualRows.map((c, idx) => (idx === i ? { ...c, [field]: value } : c)));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    const fromParticipants: Connection[] = Array.from(selected).map((i) => ({
      name: participants[i].name,
      linkedin_url: participants[i].linkedin || "",
      notes: `${participants[i].title}${participants[i].company ? ` at ${participants[i].company}` : ""}`,
    }));
    const fromManual = manualRows.filter((c) => c.name.trim() || c.linkedin_url.trim());
    await onSubmit([...fromParticipants, ...fromManual]);
    setSubmitting(false);
  };

  const totalSelected = selected.size + manualRows.filter((r) => r.name.trim()).length;

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

        {/* Header */}
        <div className="mb-1 flex items-center gap-2">
          <span className="rounded-full bg-green-100 px-2.5 py-1 text-[10px] font-semibold text-green-700">
            Attended
          </span>
        </div>
        <h2 className="mb-1 text-lg font-bold text-gray-900">{event.title}</h2>
        <p className="mb-5 text-[13px] text-gray-400">
          Select the people you met at this event
        </p>

        {/* Participant list */}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-[#1a1a1a] border-t-transparent" />
            <span className="ml-2 text-[12px] text-gray-400">Loading participants...</span>
          </div>
        ) : participants.length === 0 ? (
          <div className="rounded-xl bg-[#F7F7F4] px-4 py-5 text-center mb-4">
            <p className="text-[13px] text-gray-500">No participants found for this event</p>
            <p className="mt-1 text-[11px] text-gray-400">Add people manually below</p>
          </div>
        ) : (
          <div className="mb-4">
            {/* Select all toggle */}
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[12px] font-medium text-gray-500">
                {participants.length} participant{participants.length !== 1 ? "s" : ""}
              </span>
              <button
                onClick={selectAll}
                className="text-[11px] font-medium text-[#1a1a1a] transition-colors hover:text-gray-600"
              >
                {selected.size === participants.length ? "Deselect all" : "Select all"}
              </button>
            </div>

            {/* Scrollable list */}
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
              {participants.map((p, i) => (
                <button
                  key={p.id}
                  onClick={() => toggleSelect(i)}
                  className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left transition-all ${
                    selected.has(i)
                      ? "border-[#1a1a1a]/20 bg-[#1a1a1a]/[0.03] shadow-sm"
                      : "border-black/[0.06] bg-white hover:bg-gray-50"
                  }`}
                >
                  {/* Checkbox */}
                  <div
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition-all ${
                      selected.has(i) ? "border-[#1a1a1a] bg-[#1a1a1a]" : "border-gray-300"
                    }`}
                  >
                    {selected.has(i) && (
                      <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>

                  {/* Avatar */}
                  <div
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-white"
                    style={{ backgroundColor: p.avatar_color || "#6366f1" }}
                  >
                    {p.name.charAt(0).toUpperCase()}
                  </div>

                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-semibold text-gray-900">{p.name}</p>
                    <p className="truncate text-[11px] text-gray-400">
                      {p.title}{p.company ? ` at ${p.company}` : ""}
                    </p>
                    {p.topics.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {p.topics.slice(0, 3).map((t, j) => (
                          <span key={j} className="rounded-full bg-gray-100 px-1.5 py-0.5 text-[9px] font-medium text-gray-500">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Score badge */}
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                      p.connection_score >= 80
                        ? "bg-orange-100 text-orange-600"
                        : p.connection_score >= 50
                          ? "bg-gray-100 text-gray-600"
                          : "bg-gray-50 text-gray-400"
                    }`}
                  >
                    {p.connection_score}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Manual add section */}
        <div className="mb-4">
          <button
            onClick={() => setShowManual(!showManual)}
            className="flex items-center gap-1.5 text-[12px] font-medium text-gray-400 transition-colors hover:text-gray-600"
          >
            <svg
              className={`h-3.5 w-3.5 transition-transform ${showManual ? "rotate-90" : ""}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            Add someone not in the list
          </button>

          {showManual && (
            <div className="mt-3 space-y-2 animate-fade-in">
              {manualRows.map((row, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Name"
                    value={row.name}
                    onChange={(e) => updateManualRow(i, "name", e.target.value)}
                    className="flex-1 rounded-lg border border-black/[0.06] bg-[#F7F7F4] px-3 py-2 text-[13px] text-gray-900 placeholder:text-gray-300 outline-none focus:ring-1 focus:ring-[#1a1a1a]"
                  />
                  <input
                    type="url"
                    placeholder="LinkedIn URL"
                    value={row.linkedin_url}
                    onChange={(e) => updateManualRow(i, "linkedin_url", e.target.value)}
                    className="flex-1 rounded-lg border border-black/[0.06] bg-[#F7F7F4] px-3 py-2 text-[13px] text-gray-900 placeholder:text-gray-300 outline-none focus:ring-1 focus:ring-[#1a1a1a]"
                  />
                </div>
              ))}
              <button
                onClick={addManualRow}
                className="flex items-center gap-1 text-[11px] font-medium text-gray-400 hover:text-gray-600"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Add row
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={submitting || totalSelected === 0}
            className="rounded-xl bg-[#1a1a1a] px-5 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97] disabled:opacity-40"
          >
            {submitting ? "Saving..." : `Add ${totalSelected} Connection${totalSelected !== 1 ? "s" : ""}`}
          </button>
          <button
            onClick={async () => { setSubmitting(true); await onSubmit([]); setSubmitting(false); }}
            disabled={submitting}
            className="rounded-xl border border-black/[0.06] px-5 py-2.5 text-[13px] font-medium text-gray-500 transition-all duration-200 hover:bg-gray-50 active:scale-[0.97]"
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Event Detail Modal ─────────────────────────────────────────────────────── */

function EventModal({ event, onClose, onAttend }: { event: EventEntry; onClose: () => void; onAttend?: () => void }) {
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
              event.status === "attended"
                ? "bg-green-100 text-green-700"
                : event.paymentRequired
                  ? "bg-orange-100 text-orange-600"
                  : event.status === "applied"
                    ? "bg-[#1a1a1a] text-white"
                    : event.status === "analyzed"
                      ? "bg-blue-50 text-blue-600"
                      : "bg-gray-100 text-gray-500"
            }`}
          >
            {event.status === "attended" ? "Attended" : event.paymentRequired ? "Payment Required" : event.status === "analyzed" ? "Recommended" : event.status}
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

        {/* Event Date & Location */}
        {(eventDate || event.location) && (
          <div className="mb-3 space-y-2">
            {eventDate && (
              <div className="flex items-center gap-2 rounded-xl bg-orange-50 px-3 py-2 text-[13px] font-medium text-orange-600">
                <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {new Date(eventDate).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
              </div>
            )}
            {event.location && (
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(event.location)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-2 text-[13px] font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
              >
                <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {event.location}
              </a>
            )}
          </div>
        )}

        {/* Link */}
        {eventUrl && (
          <a
            href={eventUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mb-4 flex min-w-0 items-center gap-2 text-[13px] text-gray-500 transition-colors hover:text-[#1a1a1a]"
          >
            <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
            <span className="truncate">{eventUrl}</span>
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
          {(event.applicationStatus && event.applicationStatus !== "queued") && (
            <div className="rounded-xl bg-[#F7F7F4] p-3 space-y-1.5">
              <p className="text-[11px] font-medium text-gray-400">Application Status</p>
              <p className="text-[13px] font-medium capitalize text-gray-700">
                {event.applicationStatus}
              </p>
              {eventDate && (
                <p className="text-[12px] text-gray-500">
                  {new Date(eventDate).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" })}
                </p>
              )}
              {event.location && (
                <p className="text-[12px] text-gray-500">{event.location}</p>
              )}
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
          {onAttend && (
            <button
              onClick={onAttend}
              className="rounded-xl bg-green-600 px-5 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:bg-green-700 active:scale-[0.97]"
            >
              Mark Attended
            </button>
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
