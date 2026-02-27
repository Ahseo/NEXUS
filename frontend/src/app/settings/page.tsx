"use client";

import { useEffect, useState } from "react";
import { profile as profileApi, agent, feedback as feedbackApi, targets as targetsApi } from "@/lib/api";
import type { TargetPerson, TargetPriority } from "@/lib/types";

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
  name: "", email: "", role: "", company: "", product_description: "",
  linkedin: "", twitter: "", networking_goals: [], target_roles: [],
  target_companies: [], interests: [], preferred_event_types: [],
  max_events_per_week: 4, max_event_spend: 50, preferred_days: [],
  preferred_times: [], message_tone: "casual", auto_apply_threshold: 80,
  suggest_threshold: 50, auto_schedule_threshold: 85,
};

const goalOptions = ["Find investors", "Recruit talent", "Find customers", "Build partnerships", "Learn from experts", "Expand professional network"];
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
  const [targetList, setTargetList] = useState<TargetPerson[]>([]);
  const [showTargetForm, setShowTargetForm] = useState(false);
  const [targetForm, setTargetForm] = useState({ name: "", company: "", role: "", reason: "", priority: "medium" as TargetPriority });

  useEffect(() => {
    agent.status().then((d) => setAgentData(d as AgentStatusData)).catch(() => {});
    feedbackApi.stats().then((d) => setStats(d as FeedbackStats)).catch(() => {});
    profileApi.get().then((d) => { setP({ ...defaultProfile, ...(d as FullProfile) }); }).catch(() => {});
    targetsApi.list().then((d) => setTargetList(d as TargetPerson[])).catch(() => {});
  }, []);

  const update = (field: keyof FullProfile, value: unknown) =>
    setP((prev) => ({ ...prev, [field]: value }));

  const toggleList = (field: keyof FullProfile, item: string) => {
    const list = p[field] as string[];
    update(field, list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  };

  const handleSave = async () => {
    setSaving(true); setSaved(false);
    try {
      await profileApi.update(p as unknown as Record<string, unknown>);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ } finally { setSaving(false); }
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
    } catch { /* ignore */ }
  };

  const handleAddTarget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetForm.name || !targetForm.reason) return;
    try {
      const created = (await targetsApi.create({
        name: targetForm.name, company: targetForm.company || undefined,
        role: targetForm.role || undefined, reason: targetForm.reason, priority: targetForm.priority,
      })) as TargetPerson;
      setTargetList((prev) => [created, ...prev]);
      setTargetForm({ name: "", company: "", role: "", reason: "", priority: "medium" });
      setShowTargetForm(false);
    } catch { /* ignore */ }
  };

  const handleDeleteTarget = async (id: string) => {
    try { await targetsApi.delete(id); setTargetList((prev) => prev.filter((t) => t.id !== id)); } catch { /* ignore */ }
  };

  return (
    <div className="flex h-full flex-col animate-fade-in">
      <div className="border-b border-black/[0.04] px-6 py-5">
        <h1 className="text-xl font-bold text-gray-900">Settings</h1>
        <p className="text-[12px] text-gray-400">Profile, agent, and preferences</p>
      </div>

      <div className="mx-auto w-full max-w-2xl flex-1 space-y-6 overflow-y-auto p-6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">

      <Section title="Profile">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Name" value={p.name} onChange={(v) => update("name", v)} />
          <Field label="Email" value={p.email} onChange={(v) => update("email", v)} />
          <Field label="Role" value={p.role} onChange={(v) => update("role", v)} />
          <Field label="Company" value={p.company} onChange={(v) => update("company", v)} />
          <div className="col-span-2">
            <Field label="Product" value={p.product_description} onChange={(v) => update("product_description", v)} />
          </div>
          <Field label="LinkedIn" value={p.linkedin} onChange={(v) => update("linkedin", v)} />
          <Field label="Twitter" value={p.twitter} onChange={(v) => update("twitter", v)} />
        </div>
      </Section>

      <Section title="Networking Goals">
        <ChipGroup items={goalOptions} selected={p.networking_goals} onToggle={(item) => toggleList("networking_goals", item)} />
        <Field label="Target Roles" value={(p.target_roles || []).join(", ")} onChange={(v) => update("target_roles", v.split(",").map((s) => s.trim()).filter(Boolean))} />
        <Field label="Target Companies" value={(p.target_companies || []).join(", ")} onChange={(v) => update("target_companies", v.split(",").map((s) => s.trim()).filter(Boolean))} />
      </Section>

      <Section title="Target People">
        <div className="flex items-center justify-between -mt-1 mb-3">
          <p className="text-[11px] text-gray-400">People the agent should find at events</p>
          <button onClick={() => setShowTargetForm(!showTargetForm)} className="rounded-lg bg-[#1a1a1a] px-3 py-1.5 text-[11px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]">
            {showTargetForm ? "Cancel" : "+ Add"}
          </button>
        </div>
        {showTargetForm && (
          <form onSubmit={handleAddTarget} className="mb-4 rounded-xl border border-black/[0.06] bg-[#F7F7F4] p-3 animate-fade-in-down">
            <div className="grid grid-cols-2 gap-2.5">
              <input type="text" value={targetForm.name} onChange={(e) => setTargetForm({ ...targetForm, name: e.target.value })} placeholder="Name *" className="rounded-lg border border-black/[0.06] bg-white px-3 py-2 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
              <input type="text" value={targetForm.company} onChange={(e) => setTargetForm({ ...targetForm, company: e.target.value })} placeholder="Company" className="rounded-lg border border-black/[0.06] bg-white px-3 py-2 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
              <input type="text" value={targetForm.role} onChange={(e) => setTargetForm({ ...targetForm, role: e.target.value })} placeholder="Role" className="rounded-lg border border-black/[0.06] bg-white px-3 py-2 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
              <select value={targetForm.priority} onChange={(e) => setTargetForm({ ...targetForm, priority: e.target.value as TargetPriority })} className="rounded-lg border border-black/[0.06] bg-white px-3 py-2 text-[13px] text-gray-900 focus:border-black/10 focus:outline-none">
                <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
              </select>
              <div className="col-span-2">
                <input type="text" value={targetForm.reason} onChange={(e) => setTargetForm({ ...targetForm, reason: e.target.value })} placeholder="Reason *" className="w-full rounded-lg border border-black/[0.06] bg-white px-3 py-2 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
              </div>
            </div>
            <div className="mt-2.5 flex justify-end">
              <button type="submit" className="rounded-lg bg-[#1a1a1a] px-3.5 py-1.5 text-[12px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]">Add</button>
            </div>
          </form>
        )}
        {targetList.length === 0 ? (
          <p className="text-[13px] text-gray-400">No targets yet.</p>
        ) : (
          <div className="space-y-2 stagger-children">
            {targetList.map((target) => (
              <div key={target.id} className="flex items-center justify-between rounded-xl border border-black/[0.04] bg-white px-4 py-3 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-all duration-200 hover:shadow-md">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium text-gray-900">{target.name}</span>
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500">{target.status.replace("_", " ")}</span>
                    <span className={`text-[10px] font-semibold ${target.priority === "high" ? "text-orange-500" : target.priority === "medium" ? "text-gray-500" : "text-gray-300"}`}>{target.priority}</span>
                  </div>
                  {(target.role || target.company) && <p className="text-[11px] text-gray-400">{target.role}{target.role && target.company && " at "}{target.company}</p>}
                  <p className="text-[11px] text-gray-400">{target.reason}</p>
                </div>
                <button onClick={() => handleDeleteTarget(target.id)} className="ml-2 shrink-0 text-[11px] text-gray-300 transition-colors hover:text-red-400">Remove</button>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Event Preferences">
        <Field label="Interests" value={(p.interests || []).join(", ")} onChange={(v) => update("interests", v.split(",").map((s) => s.trim()).filter(Boolean))} />
        <ChipGroup items={eventTypeOptions} selected={p.preferred_event_types} onToggle={(item) => toggleList("preferred_event_types", item)} />
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-[11px] font-medium text-gray-400">Max Events / Week</label>
            <input type="number" min={1} max={20} value={p.max_events_per_week} onChange={(e) => update("max_events_per_week", Number(e.target.value))} className="w-full rounded-xl border border-black/[0.06] bg-white px-3 py-2.5 text-[13px] text-gray-900 focus:border-black/10 focus:outline-none" />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-medium text-gray-400">Max Spend ($)</label>
            <input type="number" min={0} max={1000} value={p.max_event_spend} onChange={(e) => update("max_event_spend", Number(e.target.value))} className="w-full rounded-xl border border-black/[0.06] bg-white px-3 py-2.5 text-[13px] text-gray-900 focus:border-black/10 focus:outline-none" />
          </div>
        </div>
        <ChipGroup items={dayOptions} selected={p.preferred_days} onToggle={(item) => toggleList("preferred_days", item)} />
        <ChipGroup items={timeOptions} selected={p.preferred_times} onToggle={(item) => toggleList("preferred_times", item)} />
        <div>
          <label className="mb-2 block text-[11px] font-medium text-gray-400">Message Tone</label>
          <div className="flex gap-2">
            {toneOptions.map((t) => (
              <button key={t} onClick={() => update("message_tone", t)} className={`rounded-full px-4 py-1.5 text-[13px] capitalize transition-all duration-200 ${p.message_tone === t ? "bg-[#1a1a1a] text-white shadow-sm" : "bg-white border border-black/[0.06] text-gray-400 hover:text-gray-600"}`}>
                {t}
              </button>
            ))}
          </div>
        </div>
      </Section>

      <Section title="Automation">
        <Slider label="Auto-Apply" value={p.auto_apply_threshold} onChange={(v) => update("auto_apply_threshold", v)} desc="Auto-apply above this score" />
        <Slider label="Suggest" value={p.suggest_threshold} onChange={(v) => update("suggest_threshold", v)} desc="Show for review above this" />
        <Slider label="Auto-Schedule" value={p.auto_schedule_threshold} onChange={(v) => update("auto_schedule_threshold", v)} desc="Auto-add to calendar above this" />
      </Section>

      <div className="flex items-center gap-3">
        <button onClick={handleSave} disabled={saving} className="rounded-xl bg-[#1a1a1a] px-6 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97] disabled:opacity-50">
          {saving ? "Saving..." : "Save Changes"}
        </button>
        {saved && <span className="text-[13px] text-gray-400 animate-fade-in">Saved</span>}
      </div>

      <Section title="Agent">
        <div className="mb-4 grid grid-cols-3 gap-3 stagger-children">
          <div className="rounded-xl bg-[#F7F7F4] p-3">
            <p className="text-[11px] font-medium text-gray-400">Status</p>
            <div className="mt-1.5 flex items-center gap-2">
              <span className={`inline-block h-2.5 w-2.5 rounded-full transition-all duration-500 ${agentData?.status === "running" ? "bg-orange-500 animate-pulse" : "bg-gray-300"}`} />
              <span className="text-[13px] font-medium capitalize text-gray-700">{agentData?.status ?? "..."}</span>
            </div>
          </div>
          <div className="rounded-xl bg-[#F7F7F4] p-3">
            <p className="text-[11px] font-medium text-gray-400">Processed</p>
            <p className="mt-1.5 text-lg font-bold text-gray-900 tabular-nums">{agentData?.events_processed ?? "--"}</p>
          </div>
          <div className="rounded-xl bg-[#F7F7F4] p-3">
            <p className="text-[11px] font-medium text-gray-400">Messages</p>
            <p className="mt-1.5 text-lg font-bold text-gray-900 tabular-nums">{agentData?.messages_sent ?? "--"}</p>
          </div>
        </div>
        {stats && (
          <div className="mb-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-[#F7F7F4] p-3">
              <p className="text-[11px] font-medium text-gray-400">Accept Rate</p>
              <p className="mt-1.5 text-lg font-bold text-gray-900">{stats.accept_rate != null ? `${Math.round(stats.accept_rate * 100)}%` : "--"}</p>
            </div>
            <div className="rounded-xl bg-[#F7F7F4] p-3">
              <p className="text-[11px] font-medium text-gray-400">Reject Rate</p>
              <p className="mt-1.5 text-lg font-bold text-gray-500">{stats.reject_rate != null ? `${Math.round(stats.reject_rate * 100)}%` : "--"}</p>
            </div>
          </div>
        )}
        <button onClick={handleToggleAgent} className={`rounded-xl px-4 py-2.5 text-[13px] font-medium transition-all duration-200 active:scale-[0.97] ${agentData?.status === "running" ? "border border-black/[0.06] bg-white text-gray-500 hover:bg-gray-50" : "bg-[#1a1a1a] text-white hover:bg-[#333]"}`}>
          {agentData?.status === "running" ? "Pause Agent" : "Resume Agent"}
        </button>
      </Section>

      <Section title="Integrations">
        <div className="space-y-2 stagger-children">
          {[{ name: "Google Calendar", connected: false }, { name: "LinkedIn", connected: false }, { name: "Twitter", connected: false }].map((i) => (
            <div key={i.name} className="flex items-center justify-between rounded-xl border border-black/[0.04] bg-white p-3.5 shadow-[0_1px_2px_rgba(0,0,0,0.02)] transition-all duration-200 hover:shadow-md">
              <span className="text-[13px] font-medium text-gray-700">{i.name}</span>
              <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${i.connected ? "bg-green-50 text-green-600" : "bg-gray-100 text-gray-400"}`}>
                {i.connected ? "Connected" : "Not connected"}
              </span>
            </div>
          ))}
        </div>
      </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-black/[0.04] bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.03)] animate-fade-in-up">
      <h2 className="mb-4 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-[11px] font-medium text-gray-400">{label}</label>
      <input type="text" value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-xl border border-black/[0.06] bg-[#F7F7F4] px-3 py-2.5 text-[13px] text-gray-900 placeholder-gray-400 transition-all duration-200 focus:border-black/10 focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/[0.04]" />
    </div>
  );
}

function ChipGroup({ items, selected, onToggle }: { items: string[]; selected: string[]; onToggle: (item: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <button key={item} onClick={() => onToggle(item)} className={`rounded-full px-3 py-1.5 text-[12px] capitalize transition-all duration-200 ${selected.includes(item) ? "bg-[#1a1a1a] text-white shadow-sm" : "border border-black/[0.06] bg-white text-gray-400 hover:border-black/10 hover:text-gray-600"}`}>
          {item.replace("_", " ")}
        </button>
      ))}
    </div>
  );
}

function Slider({ label, value, onChange, desc }: { label: string; value: number; onChange: (v: number) => void; desc: string }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="text-[13px] text-gray-700">{label}</label>
        <span className="font-mono text-[13px] font-bold text-gray-900 tabular-nums">{value}</span>
      </div>
      <input type="range" min={0} max={100} value={value} onChange={(e) => onChange(Number(e.target.value))} className="mt-2 w-full" />
      <p className="mt-1 text-[11px] text-gray-300">{desc}</p>
    </div>
  );
}
