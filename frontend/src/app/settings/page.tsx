"use client";

import { useEffect, useState } from "react";
import { profile as profileApi, agent, feedback as feedbackApi } from "@/lib/api";

interface AgentStatusData {
  status: string;
  events_processed?: number;
  messages_sent?: number;
}

interface FeedbackStats {
  total_feedback?: number;
  accept_rate?: number;
  reject_rate?: number;
}

interface FullProfile {
  name: string;
  email: string;
  role: string;
  company: string;
  product_description: string;
  linkedin: string;
  twitter: string;
  networking_goals: string[];
  target_roles: string[];
  target_companies: string[];
  interests: string[];
  preferred_event_types: string[];
  max_events_per_week: number;
  max_event_spend: number;
  preferred_days: string[];
  preferred_times: string[];
  message_tone: string;
  auto_apply_threshold: number;
  suggest_threshold: number;
  auto_schedule_threshold: number;
}

const defaultProfile: FullProfile = {
  name: "",
  email: "",
  role: "",
  company: "",
  product_description: "",
  linkedin: "",
  twitter: "",
  networking_goals: [],
  target_roles: [],
  target_companies: [],
  interests: [],
  preferred_event_types: [],
  max_events_per_week: 4,
  max_event_spend: 50,
  preferred_days: [],
  preferred_times: [],
  message_tone: "casual",
  auto_apply_threshold: 80,
  suggest_threshold: 50,
  auto_schedule_threshold: 85,
};

const goalOptions = [
  "Find investors",
  "Recruit talent",
  "Find customers",
  "Build partnerships",
  "Learn from experts",
  "Expand professional network",
];
const eventTypeOptions = ["conference", "meetup", "dinner", "workshop", "happy_hour", "demo_day"];
const dayOptions = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const timeOptions = ["Morning", "Afternoon", "Evening"];
const toneOptions = ["casual", "friendly", "professional"];

export default function SettingsPage() {
  const [agentData, setAgentData] = useState<AgentStatusData | null>(null);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [p, setP] = useState<FullProfile>(defaultProfile);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    agent.status().then((d) => setAgentData(d as AgentStatusData)).catch(() => {});
    feedbackApi.stats().then((d) => setStats(d as FeedbackStats)).catch(() => {});
    profileApi
      .get()
      .then((d) => {
        const data = d as FullProfile;
        setP({ ...defaultProfile, ...data });
      })
      .catch(() => {});
  }, []);

  const update = (field: keyof FullProfile, value: unknown) =>
    setP((prev) => ({ ...prev, [field]: value }));

  const toggleList = (field: keyof FullProfile, item: string) => {
    const list = p[field] as string[];
    update(field, list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await profileApi.update(p as unknown as Record<string, unknown>);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const handleToggleAgent = async () => {
    try {
      if (agentData?.status === "running") {
        await agent.pause();
        setAgentData((prev) => (prev ? { ...prev, status: "paused" } : prev));
      } else {
        await agent.resume();
        setAgentData((prev) => (prev ? { ...prev, status: "running" } : prev));
      }
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500">Profile, agent config, and integrations</p>
      </div>

      {/* ── Profile ─────────────────────────────────────── */}
      <Section title="Profile">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Name" value={p.name} onChange={(v) => update("name", v)} />
          <Field label="Email" value={p.email} onChange={(v) => update("email", v)} />
          <Field label="Role" value={p.role} onChange={(v) => update("role", v)} />
          <Field label="Company" value={p.company} onChange={(v) => update("company", v)} />
          <div className="col-span-2">
            <Field
              label="Product Description"
              value={p.product_description}
              onChange={(v) => update("product_description", v)}
            />
          </div>
          <Field label="LinkedIn" value={p.linkedin} onChange={(v) => update("linkedin", v)} />
          <Field label="Twitter" value={p.twitter} onChange={(v) => update("twitter", v)} />
        </div>
      </Section>

      {/* ── Networking Goals ─────────────────────────────── */}
      <Section title="Networking Goals">
        <ChipGroup
          label="Goals"
          items={goalOptions}
          selected={p.networking_goals}
          onToggle={(item) => toggleList("networking_goals", item)}
        />
        <Field
          label="Target Roles (comma-separated)"
          value={(p.target_roles || []).join(", ")}
          onChange={(v) =>
            update(
              "target_roles",
              v.split(",").map((s) => s.trim()).filter(Boolean)
            )
          }
        />
        <Field
          label="Target Companies (comma-separated)"
          value={(p.target_companies || []).join(", ")}
          onChange={(v) =>
            update(
              "target_companies",
              v.split(",").map((s) => s.trim()).filter(Boolean)
            )
          }
        />
      </Section>

      {/* ── Event Preferences ─────────────────────────────── */}
      <Section title="Event Preferences">
        <Field
          label="Interests (comma-separated)"
          value={(p.interests || []).join(", ")}
          onChange={(v) =>
            update(
              "interests",
              v.split(",").map((s) => s.trim()).filter(Boolean)
            )
          }
        />
        <ChipGroup
          label="Event Types"
          items={eventTypeOptions}
          selected={p.preferred_event_types}
          onToggle={(item) => toggleList("preferred_event_types", item)}
        />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-xs text-gray-500">Max Events / Week</label>
            <input
              type="number"
              min={1}
              max={20}
              value={p.max_events_per_week}
              onChange={(e) => update("max_events_per_week", Number(e.target.value))}
              className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-500">Max Spend / Event ($)</label>
            <input
              type="number"
              min={0}
              max={1000}
              value={p.max_event_spend}
              onChange={(e) => update("max_event_spend", Number(e.target.value))}
              className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none"
            />
          </div>
        </div>
        <ChipGroup
          label="Preferred Days"
          items={dayOptions}
          selected={p.preferred_days}
          onToggle={(item) => toggleList("preferred_days", item)}
        />
        <ChipGroup
          label="Preferred Times"
          items={timeOptions}
          selected={p.preferred_times}
          onToggle={(item) => toggleList("preferred_times", item)}
        />
        <div>
          <label className="mb-2 block text-xs text-gray-500">Message Tone</label>
          <div className="flex gap-2">
            {toneOptions.map((t) => (
              <button
                key={t}
                onClick={() => update("message_tone", t)}
                className={`rounded-full px-4 py-1 text-sm capitalize transition ${
                  p.message_tone === t
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:text-gray-200"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Automation Thresholds ─────────────────────────── */}
      <Section title="Automation Thresholds">
        <Slider
          label="Auto-Apply Threshold"
          value={p.auto_apply_threshold}
          onChange={(v) => update("auto_apply_threshold", v)}
          desc="Events scoring above this are automatically applied to"
        />
        <Slider
          label="Suggest Threshold"
          value={p.suggest_threshold}
          onChange={(v) => update("suggest_threshold", v)}
          desc="Events scoring above this are shown for review"
        />
        <Slider
          label="Auto-Schedule Threshold"
          value={p.auto_schedule_threshold}
          onChange={(v) => update("auto_schedule_threshold", v)}
          desc="Confirmed events above this are auto-added to calendar"
        />
      </Section>

      {/* ── Save Button ─────────────────────────────── */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save All Changes"}
        </button>
        {saved && <span className="text-sm text-green-400">Saved!</span>}
      </div>

      {/* ── Agent Status ─────────────────────────────── */}
      <Section title="Agent Performance">
        <div className="mb-4 grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-gray-500">Status</p>
            <div className="mt-1 flex items-center gap-2">
              <span
                className={`inline-block h-2.5 w-2.5 rounded-full ${
                  agentData?.status === "running" ? "bg-green-500" : "bg-yellow-500"
                }`}
              />
              <span className="text-sm font-medium capitalize text-gray-200">
                {agentData?.status ?? "unknown"}
              </span>
            </div>
          </div>
          <div>
            <p className="text-xs text-gray-500">Events Processed</p>
            <p className="mt-1 text-lg font-bold text-gray-200">
              {agentData?.events_processed ?? "--"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Messages Sent</p>
            <p className="mt-1 text-lg font-bold text-gray-200">
              {agentData?.messages_sent ?? "--"}
            </p>
          </div>
        </div>
        {stats && (
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Accept Rate</p>
              <p className="mt-1 text-lg font-bold text-green-400">
                {stats.accept_rate != null ? `${Math.round(stats.accept_rate * 100)}%` : "--"}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Reject Rate</p>
              <p className="mt-1 text-lg font-bold text-red-400">
                {stats.reject_rate != null ? `${Math.round(stats.reject_rate * 100)}%` : "--"}
              </p>
            </div>
          </div>
        )}
        <button
          onClick={handleToggleAgent}
          className={`rounded px-4 py-2 text-sm font-medium text-white ${
            agentData?.status === "running"
              ? "bg-yellow-600 hover:bg-yellow-500"
              : "bg-green-600 hover:bg-green-500"
          }`}
        >
          {agentData?.status === "running" ? "Pause Agent" : "Resume Agent"}
        </button>
      </Section>

      {/* ── Integrations ─────────────────────────────── */}
      <Section title="Integrations">
        <div className="space-y-3">
          {[
            { name: "Google Calendar", connected: false },
            { name: "LinkedIn", connected: false },
            { name: "Twitter", connected: false },
          ].map((integration) => (
            <div
              key={integration.name}
              className="flex items-center justify-between rounded border border-gray-800 p-3"
            >
              <span className="text-sm text-gray-200">{integration.name}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  integration.connected
                    ? "bg-green-900 text-green-300"
                    : "bg-gray-700 text-gray-400"
                }`}
              >
                {integration.connected ? "Connected" : "Not connected"}
              </span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Reusable Components ─────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-gray-800 bg-gray-900 p-5">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-gray-500">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
      />
    </div>
  );
}

function ChipGroup({
  label,
  items,
  selected,
  onToggle,
}: {
  label: string;
  items: string[];
  selected: string[];
  onToggle: (item: string) => void;
}) {
  return (
    <div>
      <label className="mb-2 block text-xs text-gray-500">{label}</label>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <button
            key={item}
            onClick={() => onToggle(item)}
            className={`rounded-full px-3 py-1 text-sm capitalize transition ${
              selected.includes(item)
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-gray-200"
            }`}
          >
            {item.replace("_", " ")}
          </button>
        ))}
      </div>
    </div>
  );
}

function Slider({
  label,
  value,
  onChange,
  desc,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  desc: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="text-sm text-gray-300">{label}</label>
        <span className="font-mono text-sm text-indigo-400">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full accent-indigo-500"
      />
      <p className="mt-1 text-xs text-gray-600">{desc}</p>
    </div>
  );
}
