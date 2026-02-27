"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { profile as profileApi } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import type { MessageTone, TargetPriority } from "@/lib/types";

const STEPS = ["About You", "Goals", "Events", "Automation"];

const goalOptions = ["Find investors", "Recruit talent", "Find customers", "Build partnerships", "Learn from experts", "Expand professional network"];
const eventTypeOptions = ["conference", "meetup", "dinner", "workshop", "happy_hour", "demo_day"];
const dayOptions = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const timeOptions = ["Morning", "Afternoon", "Evening"];

interface TargetInput { name: string; company: string; reason: string; priority: TargetPriority }

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [company, setCompany] = useState("");
  const [product, setProduct] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [twitter, setTwitter] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => { if (user?.email) setEmail(user.email); }, [user]);

  const [goals, setGoals] = useState<string[]>([]);
  const [targetRoles, setTargetRoles] = useState("");
  const [targetCompanies, setTargetCompanies] = useState("");
  const [targetPeople, setTargetPeople] = useState<TargetInput[]>([]);
  const [newTarget, setNewTarget] = useState<TargetInput>({ name: "", company: "", reason: "", priority: "medium" });

  const [interests, setInterests] = useState("");
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [maxEvents, setMaxEvents] = useState(5);
  const [maxSpend, setMaxSpend] = useState(200);
  const [preferredDays, setPreferredDays] = useState<string[]>([]);
  const [preferredTimes, setPreferredTimes] = useState<string[]>([]);

  const [autoApply, setAutoApply] = useState(85);
  const [suggestThreshold, setSuggestThreshold] = useState(60);
  const [autoSchedule, setAutoSchedule] = useState(90);
  const [messageTone, setMessageTone] = useState<MessageTone>("friendly");

  const toggleItem = (list: string[], setter: (v: string[]) => void, item: string) => {
    setter(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  const addTarget = () => {
    if (!newTarget.name || !newTarget.reason) return;
    setTargetPeople([...targetPeople, newTarget]);
    setNewTarget({ name: "", company: "", reason: "", priority: "medium" });
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      await profileApi.update({
        name, email, role, company, product_description: product, linkedin, twitter,
        networking_goals: goals,
        target_roles: targetRoles.split(",").map((s) => s.trim()).filter(Boolean),
        target_companies: targetCompanies.split(",").map((s) => s.trim()).filter(Boolean),
        interests: interests.split(",").map((s) => s.trim()).filter(Boolean),
        preferred_event_types: eventTypes, max_events_per_week: maxEvents, max_event_spend: maxSpend,
        preferred_days: preferredDays, preferred_times: preferredTimes, message_tone: messageTone,
        auto_apply_threshold: autoApply, suggest_threshold: suggestThreshold, auto_schedule_threshold: autoSchedule,
      });
      router.push("/");
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F7F7F4] p-6">
      <div className="w-full max-w-xl animate-fade-in">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#1a1a1a] shadow-lg animate-float">
            <span className="text-lg font-bold text-white">W</span>
          </div>
          <h1 className="text-2xl font-bold text-[#1a1a1a]">Set up WINGMAN</h1>
          <p className="mt-1 text-[13px] text-gray-400">Configure your networking agent</p>
        </div>

        {/* Progress */}
        <div className="mb-6 flex items-center gap-2">
          {STEPS.map((s, i) => (
            <div key={s} className="flex flex-1 flex-col items-center">
              <div className={`mb-1 h-1 w-full rounded-full transition-all duration-500 ${i <= step ? "bg-[#1a1a1a]" : "bg-black/[0.06]"}`} />
              <span className={`text-[10px] transition-colors duration-300 ${i === step ? "text-gray-900 font-medium" : "text-gray-400"}`}>{s}</span>
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="glass-strong rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)] animate-scale-in" key={step}>
          {step === 0 && (
            <div className="space-y-3.5">
              <h2 className="text-lg font-semibold text-gray-900">About You</h2>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Name *" value={name} onChange={setName} placeholder="Jane Doe" />
                <Input label="Email *" value={email} onChange={setEmail} placeholder="jane@acme.com" type="email" />
                <Input label="Role" value={role} onChange={setRole} placeholder="CEO" />
                <Input label="Company" value={company} onChange={setCompany} placeholder="Acme Inc" />
                <div className="col-span-2"><Input label="Product" value={product} onChange={setProduct} placeholder="We build AI-powered..." /></div>
                <Input label="LinkedIn" value={linkedin} onChange={setLinkedin} placeholder="linkedin.com/in/..." />
                <Input label="Twitter" value={twitter} onChange={setTwitter} placeholder="@janedoe" />
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Goals</h2>
              <div>
                <label className="mb-2 block text-[11px] font-medium text-gray-400">What are you looking for?</label>
                <div className="flex flex-wrap gap-2">
                  {goalOptions.map((g) => (
                    <button key={g} onClick={() => toggleItem(goals, setGoals, g)} className={`rounded-full px-3.5 py-1.5 text-[13px] transition-all duration-200 ${goals.includes(g) ? "bg-[#1a1a1a] text-white shadow-sm" : "border border-black/[0.06] bg-white text-gray-400 hover:text-gray-600"}`}>{g}</button>
                  ))}
                </div>
              </div>
              <Input label="Target Roles" value={targetRoles} onChange={setTargetRoles} placeholder="CTO, VP Engineering, Founder" />
              <Input label="Target Companies" value={targetCompanies} onChange={setTargetCompanies} placeholder="Google, Stripe, OpenAI" />
              <div>
                <label className="mb-2 block text-[11px] font-medium text-gray-400">Target People</label>
                {targetPeople.map((t, i) => (
                  <div key={i} className="mb-2 flex items-center justify-between rounded-xl bg-[#F7F7F4] px-3 py-2 text-[13px] text-gray-600">
                    <span>{t.name} {t.company && `(${t.company})`}</span>
                    <button onClick={() => setTargetPeople(targetPeople.filter((_, j) => j !== i))} className="text-[11px] text-gray-300 hover:text-red-400">Remove</button>
                  </div>
                ))}
                <div className="grid grid-cols-4 gap-2">
                  <input type="text" value={newTarget.name} onChange={(e) => setNewTarget({ ...newTarget, name: e.target.value })} placeholder="Name" className="rounded-lg border border-black/[0.06] bg-white px-2.5 py-1.5 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
                  <input type="text" value={newTarget.company} onChange={(e) => setNewTarget({ ...newTarget, company: e.target.value })} placeholder="Company" className="rounded-lg border border-black/[0.06] bg-white px-2.5 py-1.5 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
                  <input type="text" value={newTarget.reason} onChange={(e) => setNewTarget({ ...newTarget, reason: e.target.value })} placeholder="Reason" className="rounded-lg border border-black/[0.06] bg-white px-2.5 py-1.5 text-[13px] text-gray-900 placeholder-gray-400 focus:border-black/10 focus:outline-none" />
                  <button onClick={addTarget} className="rounded-lg bg-gray-100 px-2.5 py-1.5 text-[13px] text-gray-500 transition-all hover:bg-gray-200">Add</button>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Events</h2>
              <Input label="Interests" value={interests} onChange={setInterests} placeholder="AI, SaaS, Fintech" />
              <div>
                <label className="mb-2 block text-[11px] font-medium text-gray-400">Event Types</label>
                <div className="flex flex-wrap gap-2">
                  {eventTypeOptions.map((t) => (
                    <button key={t} onClick={() => toggleItem(eventTypes, setEventTypes, t)} className={`rounded-full px-3.5 py-1.5 text-[13px] capitalize transition-all duration-200 ${eventTypes.includes(t) ? "bg-[#1a1a1a] text-white shadow-sm" : "border border-black/[0.06] bg-white text-gray-400 hover:text-gray-600"}`}>{t.replace("_", " ")}</button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-[11px] font-medium text-gray-400">Max Events / Week</label>
                  <input type="number" min={1} max={20} value={maxEvents} onChange={(e) => setMaxEvents(Number(e.target.value))} className="w-full rounded-xl border border-black/[0.06] bg-white px-3 py-2.5 text-[13px] text-gray-900 focus:border-black/10 focus:outline-none" />
                </div>
                <div>
                  <label className="mb-1 block text-[11px] font-medium text-gray-400">Max Spend ($)</label>
                  <input type="number" min={0} max={1000} value={maxSpend} onChange={(e) => setMaxSpend(Number(e.target.value))} className="w-full rounded-xl border border-black/[0.06] bg-white px-3 py-2.5 text-[13px] text-gray-900 focus:border-black/10 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="mb-2 block text-[11px] font-medium text-gray-400">Preferred Days</label>
                <div className="flex flex-wrap gap-2">
                  {dayOptions.map((d) => (
                    <button key={d} onClick={() => toggleItem(preferredDays, setPreferredDays, d)} className={`rounded-full px-3 py-1.5 text-[13px] transition-all duration-200 ${preferredDays.includes(d) ? "bg-[#1a1a1a] text-white shadow-sm" : "border border-black/[0.06] bg-white text-gray-400 hover:text-gray-600"}`}>{d}</button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-2 block text-[11px] font-medium text-gray-400">Preferred Times</label>
                <div className="flex flex-wrap gap-2">
                  {timeOptions.map((t) => (
                    <button key={t} onClick={() => toggleItem(preferredTimes, setPreferredTimes, t)} className={`rounded-full px-3 py-1.5 text-[13px] transition-all duration-200 ${preferredTimes.includes(t) ? "bg-[#1a1a1a] text-white shadow-sm" : "border border-black/[0.06] bg-white text-gray-400 hover:text-gray-600"}`}>{t}</button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-gray-900">Automation</h2>
              <div>
                <div className="flex items-center justify-between"><label className="text-[13px] text-gray-700">Auto-Apply</label><span className="font-mono text-[13px] font-bold text-gray-900">{autoApply}</span></div>
                <input type="range" min={0} max={100} value={autoApply} onChange={(e) => setAutoApply(Number(e.target.value))} className="mt-2 w-full" />
                <p className="mt-1 text-[11px] text-gray-300">Auto-apply above this score</p>
              </div>
              <div>
                <div className="flex items-center justify-between"><label className="text-[13px] text-gray-700">Suggest</label><span className="font-mono text-[13px] font-bold text-gray-900">{suggestThreshold}</span></div>
                <input type="range" min={0} max={100} value={suggestThreshold} onChange={(e) => setSuggestThreshold(Number(e.target.value))} className="mt-2 w-full" />
              </div>
              <div>
                <div className="flex items-center justify-between"><label className="text-[13px] text-gray-700">Auto-Schedule</label><span className="font-mono text-[13px] font-bold text-gray-900">{autoSchedule}</span></div>
                <input type="range" min={0} max={100} value={autoSchedule} onChange={(e) => setAutoSchedule(Number(e.target.value))} className="mt-2 w-full" />
              </div>
              <div>
                <label className="mb-2 block text-[11px] font-medium text-gray-400">Message Tone</label>
                <div className="flex gap-2">
                  {(["casual", "friendly", "professional"] as MessageTone[]).map((t) => (
                    <button key={t} onClick={() => setMessageTone(t)} className={`rounded-full px-4 py-1.5 text-[13px] capitalize transition-all duration-200 ${messageTone === t ? "bg-[#1a1a1a] text-white shadow-sm" : "border border-black/[0.06] bg-white text-gray-400 hover:text-gray-600"}`}>{t}</button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <button onClick={() => setStep(step - 1)} disabled={step === 0} className="rounded-xl px-4 py-2 text-[13px] font-medium text-gray-400 transition-colors hover:text-gray-700 disabled:invisible">
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button onClick={() => setStep(step + 1)} className="rounded-xl bg-[#1a1a1a] px-6 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]">
              Next
            </button>
          ) : (
            <button onClick={handleFinish} disabled={saving} className="rounded-xl bg-[#1a1a1a] px-6 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97] disabled:opacity-50">
              {saving ? "..." : "Finish"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, placeholder, type = "text" }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <div>
      <label className="mb-1 block text-[11px] font-medium text-gray-400">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full rounded-xl border border-black/[0.06] bg-[#F7F7F4] px-3 py-2.5 text-[13px] text-gray-900 placeholder-gray-400 transition-all duration-200 focus:border-black/10 focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/[0.04]" />
    </div>
  );
}
