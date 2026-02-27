"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { profile as profileApi } from "@/lib/api";
import type { MessageTone, TargetPriority } from "@/lib/types";

const STEPS = ["About You", "Networking Goals", "Event Preferences", "Automation Level"];

const goalOptions = [
  "Find investors",
  "Recruit talent",
  "Find customers",
  "Build partnerships",
  "Learn from experts",
  "Expand professional network",
];

const eventTypeOptions = [
  "conference",
  "meetup",
  "dinner",
  "workshop",
  "happy_hour",
  "demo_day",
];

const dayOptions = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const timeOptions = ["Morning", "Afternoon", "Evening"];

interface TargetInput {
  name: string;
  company: string;
  reason: string;
  priority: TargetPriority;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);

  // Step 1
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [company, setCompany] = useState("");
  const [product, setProduct] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [twitter, setTwitter] = useState("");
  const [email, setEmail] = useState("");

  // Step 2
  const [goals, setGoals] = useState<string[]>([]);
  const [targetRoles, setTargetRoles] = useState("");
  const [targetCompanies, setTargetCompanies] = useState("");
  const [targetPeople, setTargetPeople] = useState<TargetInput[]>([]);
  const [newTarget, setNewTarget] = useState<TargetInput>({
    name: "",
    company: "",
    reason: "",
    priority: "medium",
  });

  // Step 3
  const [interests, setInterests] = useState("");
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [maxEvents, setMaxEvents] = useState(5);
  const [maxSpend, setMaxSpend] = useState(200);
  const [preferredDays, setPreferredDays] = useState<string[]>([]);
  const [preferredTimes, setPreferredTimes] = useState<string[]>([]);

  // Step 4
  const [autoApply, setAutoApply] = useState(85);
  const [suggestThreshold, setSuggestThreshold] = useState(60);
  const [autoSchedule, setAutoSchedule] = useState(90);
  const [messageTone, setMessageTone] = useState<MessageTone>("friendly");

  const toggleItem = (
    list: string[],
    setter: (v: string[]) => void,
    item: string
  ) => {
    setter(
      list.includes(item) ? list.filter((i) => i !== item) : [...list, item]
    );
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
        name,
        email,
        role,
        company,
        product_description: product,
        linkedin,
        twitter,
        networking_goals: goals,
        target_roles: targetRoles
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        target_companies: targetCompanies
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        interests: interests
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        preferred_event_types: eventTypes,
        max_events_per_week: maxEvents,
        max_event_spend: maxSpend,
        preferred_days: preferredDays,
        preferred_times: preferredTimes,
        message_tone: messageTone,
        auto_apply_threshold: autoApply,
        suggest_threshold: suggestThreshold,
        auto_schedule_threshold: autoSchedule,
      });
      router.push("/");
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 p-6">
      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-indigo-400">NEXUS</h1>
          <p className="mt-1 text-sm text-gray-500">
            Set up your networking agent
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8 flex items-center gap-2">
          {STEPS.map((s, i) => (
            <div key={s} className="flex flex-1 flex-col items-center">
              <div
                className={`mb-1 h-1 w-full rounded-full ${
                  i <= step ? "bg-indigo-500" : "bg-gray-800"
                }`}
              />
              <span
                className={`text-[10px] ${
                  i === step ? "text-indigo-400" : "text-gray-600"
                }`}
              >
                {s}
              </span>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          {step === 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-100">About You</h2>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Name *" value={name} onChange={setName} placeholder="Jane Doe" />
                <Input label="Email *" value={email} onChange={setEmail} placeholder="jane@acme.com" type="email" />
                <Input label="Role" value={role} onChange={setRole} placeholder="CEO" />
                <Input label="Company" value={company} onChange={setCompany} placeholder="Acme Inc" />
                <div className="col-span-2">
                  <Input label="Product Description" value={product} onChange={setProduct} placeholder="We build AI-powered widgets for..." />
                </div>
                <Input label="LinkedIn URL" value={linkedin} onChange={setLinkedin} placeholder="https://linkedin.com/in/..." />
                <Input label="Twitter Handle" value={twitter} onChange={setTwitter} placeholder="@janedoe" />
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-100">
                Networking Goals
              </h2>
              <div>
                <label className="mb-2 block text-xs text-gray-500">
                  What are you looking for?
                </label>
                <div className="flex flex-wrap gap-2">
                  {goalOptions.map((g) => (
                    <button
                      key={g}
                      onClick={() => toggleItem(goals, setGoals, g)}
                      className={`rounded-full px-3 py-1 text-sm transition ${
                        goals.includes(g)
                          ? "bg-indigo-600 text-white"
                          : "bg-gray-800 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
              <Input
                label="Target Roles (comma-separated)"
                value={targetRoles}
                onChange={setTargetRoles}
                placeholder="CTO, VP Engineering, Founder"
              />
              <Input
                label="Target Companies (comma-separated)"
                value={targetCompanies}
                onChange={setTargetCompanies}
                placeholder="Google, Stripe, OpenAI"
              />

              {/* Target People */}
              <div>
                <label className="mb-2 block text-xs text-gray-500">
                  Target People
                </label>
                {targetPeople.map((t, i) => (
                  <div
                    key={i}
                    className="mb-2 flex items-center justify-between rounded bg-gray-800 px-3 py-2 text-sm text-gray-300"
                  >
                    <span>
                      {t.name} {t.company && `(${t.company})`} - {t.priority}
                    </span>
                    <button
                      onClick={() =>
                        setTargetPeople(targetPeople.filter((_, j) => j !== i))
                      }
                      className="text-xs text-gray-600 hover:text-red-400"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="grid grid-cols-4 gap-2">
                  <input
                    type="text"
                    value={newTarget.name}
                    onChange={(e) =>
                      setNewTarget({ ...newTarget, name: e.target.value })
                    }
                    placeholder="Name"
                    className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={newTarget.company}
                    onChange={(e) =>
                      setNewTarget({ ...newTarget, company: e.target.value })
                    }
                    placeholder="Company"
                    className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={newTarget.reason}
                    onChange={(e) =>
                      setNewTarget({ ...newTarget, reason: e.target.value })
                    }
                    placeholder="Reason"
                    className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                  />
                  <button
                    onClick={addTarget}
                    className="rounded bg-gray-700 px-2 py-1 text-sm text-gray-300 hover:bg-gray-600"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-100">
                Event Preferences
              </h2>
              <Input
                label="Interests (comma-separated)"
                value={interests}
                onChange={setInterests}
                placeholder="AI, SaaS, Fintech, Web3"
              />
              <div>
                <label className="mb-2 block text-xs text-gray-500">
                  Preferred Event Types
                </label>
                <div className="flex flex-wrap gap-2">
                  {eventTypeOptions.map((t) => (
                    <button
                      key={t}
                      onClick={() => toggleItem(eventTypes, setEventTypes, t)}
                      className={`rounded-full px-3 py-1 text-sm capitalize transition ${
                        eventTypes.includes(t)
                          ? "bg-indigo-600 text-white"
                          : "bg-gray-800 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {t.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs text-gray-500">
                    Max Events / Week
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={maxEvents}
                    onChange={(e) => setMaxEvents(Number(e.target.value))}
                    className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-500">
                    Max Spend / Event ($)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={1000}
                    value={maxSpend}
                    onChange={(e) => setMaxSpend(Number(e.target.value))}
                    className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="mb-2 block text-xs text-gray-500">
                  Preferred Days
                </label>
                <div className="flex flex-wrap gap-2">
                  {dayOptions.map((d) => (
                    <button
                      key={d}
                      onClick={() =>
                        toggleItem(preferredDays, setPreferredDays, d)
                      }
                      className={`rounded-full px-3 py-1 text-sm transition ${
                        preferredDays.includes(d)
                          ? "bg-indigo-600 text-white"
                          : "bg-gray-800 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-2 block text-xs text-gray-500">
                  Preferred Times
                </label>
                <div className="flex flex-wrap gap-2">
                  {timeOptions.map((t) => (
                    <button
                      key={t}
                      onClick={() =>
                        toggleItem(preferredTimes, setPreferredTimes, t)
                      }
                      className={`rounded-full px-3 py-1 text-sm transition ${
                        preferredTimes.includes(t)
                          ? "bg-indigo-600 text-white"
                          : "bg-gray-800 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-gray-100">
                Automation Level
              </h2>
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">
                    Event Application Mode
                  </label>
                  <span className="text-sm font-mono text-indigo-400">
                    {autoApply}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={autoApply}
                  onChange={(e) => setAutoApply(Number(e.target.value))}
                  className="mt-2 w-full accent-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-600">
                  Auto-apply to events scoring above this threshold
                </p>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">
                    Suggest Threshold
                  </label>
                  <span className="text-sm font-mono text-indigo-400">
                    {suggestThreshold}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={suggestThreshold}
                  onChange={(e) => setSuggestThreshold(Number(e.target.value))}
                  className="mt-2 w-full accent-indigo-500"
                />
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">
                    Calendar Auto-Schedule
                  </label>
                  <span className="text-sm font-mono text-indigo-400">
                    {autoSchedule}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={autoSchedule}
                  onChange={(e) => setAutoSchedule(Number(e.target.value))}
                  className="mt-2 w-full accent-indigo-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">
                  Cold Message Tone
                </label>
                <div className="flex gap-2">
                  {(["casual", "friendly", "professional"] as MessageTone[]).map(
                    (t) => (
                      <button
                        key={t}
                        onClick={() => setMessageTone(t)}
                        className={`rounded-full px-4 py-1 text-sm capitalize transition ${
                          messageTone === t
                            ? "bg-indigo-600 text-white"
                            : "bg-gray-800 text-gray-400 hover:text-gray-200"
                        }`}
                      >
                        {t}
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setStep(step - 1)}
            disabled={step === 0}
            className="rounded px-4 py-2 text-sm font-medium text-gray-400 hover:text-gray-200 disabled:invisible"
          >
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="rounded bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleFinish}
              disabled={saving}
              className="rounded bg-green-600 px-6 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Finish Setup"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-gray-500">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
      />
    </div>
  );
}
