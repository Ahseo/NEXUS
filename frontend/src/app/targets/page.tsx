"use client";

import { useEffect, useState } from "react";
import { targets as targetsApi } from "@/lib/api";
import type { TargetPerson, TargetPriority } from "@/lib/types";

const statusColors: Record<string, string> = {
  searching: "bg-blue-900 text-blue-300",
  found_event: "bg-indigo-900 text-indigo-300",
  messaged: "bg-yellow-900 text-yellow-300",
  connected: "bg-green-900 text-green-300",
};

const priorityColors: Record<string, string> = {
  high: "text-red-400",
  medium: "text-yellow-400",
  low: "text-gray-400",
};

export default function TargetsPage() {
  const [targetList, setTargetList] = useState<TargetPerson[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "",
    company: "",
    role: "",
    reason: "",
    priority: "medium" as TargetPriority,
  });

  useEffect(() => {
    targetsApi
      .list()
      .then((data) => setTargetList(data as TargetPerson[]))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.reason) return;
    try {
      const created = (await targetsApi.create({
        name: form.name,
        company: form.company || undefined,
        role: form.role || undefined,
        reason: form.reason,
        priority: form.priority,
      })) as TargetPerson;
      setTargetList((prev) => [created, ...prev]);
      setForm({ name: "", company: "", role: "", reason: "", priority: "medium" });
      setShowForm(false);
    } catch {
      /* ignore */
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await targetsApi.delete(id);
      setTargetList((prev) => prev.filter((t) => t.id !== id));
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Target People</h1>
          <p className="text-sm text-gray-500">
            People you want the agent to find at events
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          {showForm ? "Cancel" : "+ Add Target"}
        </button>
      </div>

      {/* Add Target Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 rounded-lg border border-gray-800 bg-gray-900 p-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-xs text-gray-500">Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                placeholder="John Doe"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Company</label>
              <input
                type="text"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                placeholder="Acme Inc"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Role</label>
              <input
                type="text"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                placeholder="VP of Engineering"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Priority</label>
              <select
                value={form.priority}
                onChange={(e) =>
                  setForm({ ...form, priority: e.target.value as TargetPriority })
                }
                className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="mb-1 block text-xs text-gray-500">
                Reason *
              </label>
              <input
                type="text"
                value={form.reason}
                onChange={(e) => setForm({ ...form, reason: e.target.value })}
                className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                placeholder="Potential investor, interested in our Series A"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Add Target
            </button>
          </div>
        </form>
      )}

      {/* Target List */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-gray-500">
          Loading targets...
        </div>
      ) : targetList.length === 0 ? (
        <p className="text-sm text-gray-600">No target people added yet.</p>
      ) : (
        <div className="space-y-3">
          {targetList.map((target) => (
            <div
              key={target.id}
              className="rounded-lg border border-gray-800 bg-gray-900 p-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-gray-100">{target.name}</p>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        statusColors[target.status] ?? "bg-gray-700 text-gray-300"
                      }`}
                    >
                      {target.status.replace("_", " ")}
                    </span>
                    <span
                      className={`text-xs font-medium ${
                        priorityColors[target.priority] ?? "text-gray-400"
                      }`}
                    >
                      {target.priority}
                    </span>
                  </div>
                  {(target.role || target.company) && (
                    <p className="text-sm text-gray-500">
                      {target.role}
                      {target.role && target.company && " at "}
                      {target.company}
                    </p>
                  )}
                  <p className="mt-1 text-sm text-gray-400">{target.reason}</p>
                </div>
                <button
                  onClick={() => handleDelete(target.id)}
                  className="text-xs text-gray-600 hover:text-red-400"
                >
                  Remove
                </button>
              </div>
              {target.matched_events && target.matched_events.length > 0 && (
                <div className="mt-3 border-t border-gray-800 pt-3">
                  <p className="mb-1 text-xs text-gray-500">Matched Events</p>
                  <div className="flex flex-wrap gap-2">
                    {target.matched_events.map((ev) => (
                      <a
                        key={ev.id}
                        href={`/events/${ev.id}`}
                        className="rounded bg-gray-800 px-2 py-1 text-xs text-indigo-400 hover:text-indigo-300"
                      >
                        {ev.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
