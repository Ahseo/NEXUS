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

  // Client-side filter based on score heuristic (real app would have backend status)
  const filtered = people.filter(() => {
    if (tab === "all") return true;
    // Without backend status field, show all for non-"all" tabs
    return true;
  });

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100">People</h1>
        <p className="text-sm text-gray-500">People discovered across events</p>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6 flex gap-1 rounded-lg bg-gray-900 p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition ${
              tab === t.key
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center text-gray-500">
          Loading people...
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-600">No people found.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((person) => (
            <PersonCard key={person.id} person={person} />
          ))}
        </div>
      )}
    </div>
  );
}
