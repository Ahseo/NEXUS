"use client";

import { useEffect, useState } from "react";
import { people as peopleApi } from "@/lib/api";
import type { Person } from "@/lib/types";
import PersonCard from "@/components/PersonCard";

type FilterTab = "all" | "want_to_meet" | "met" | "connected";

export default function PeoplePage() {
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<FilterTab>("all");

  useEffect(() => {
    peopleApi
      .list()
      .then((data) => setPeople(data as Person[]))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const tabs: { key: FilterTab; label: string }[] = [
    { key: "all", label: "All" },
    { key: "want_to_meet", label: "Want to Meet" },
    { key: "met", label: "Met" },
    { key: "connected", label: "Connected" },
  ];

  const filtered = people.filter(() => {
    if (tab === "all") return true;
    return true;
  });

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">People</h1>
          <p className="text-[13px] text-gray-400">People discovered across events</p>
        </div>
        <span className="rounded-full bg-[#F7F7F4] px-3 py-1 text-[12px] font-medium text-gray-400 tabular-nums">
          {filtered.length} people
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6 flex gap-1.5">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-all duration-200 ${
              tab === t.key
                ? "bg-[#1a1a1a] text-white shadow-sm"
                : "text-gray-400 hover:bg-black/[0.04] hover:text-gray-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div
              key={n}
              className="h-36 rounded-2xl bg-white/60 animate-pulse"
              style={{ animationDelay: `${n * 80}ms` }}
            />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex h-60 flex-col items-center justify-center text-center animate-fade-in">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#F7F7F4]">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-300">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <p className="text-sm text-gray-400">No people found</p>
          <p className="mt-1 text-[12px] text-gray-300">
            People will appear here as events are discovered
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 stagger-children">
          {filtered.map((person) => (
            <PersonCard key={person.id} person={person} />
          ))}
        </div>
      )}
    </div>
  );
}
