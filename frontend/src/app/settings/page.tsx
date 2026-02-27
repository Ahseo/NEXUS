"use client";

import { useEffect, useState } from "react";
import { profile as profileApi, agent, feedback as feedbackApi } from "@/lib/api";

interface AgentStatusData {
  status: string;
  events_processed?: number;
  messages_sent?: number;
  uptime?: string;
}

interface FeedbackStats {
  total_feedback?: number;
  accept_rate?: number;
  reject_rate?: number;
}

interface ProfileData {
  auto_apply_threshold: number;
  suggest_threshold: number;
  auto_schedule_threshold: number;
}

export default function SettingsPage() {
  const [agentData, setAgentData] = useState<AgentStatusData | null>(null);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [profileData, setProfileData] = useState<ProfileData>({
    auto_apply_threshold: 85,
    suggest_threshold: 60,
    auto_schedule_threshold: 90,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    agent.status().then((d) => setAgentData(d as AgentStatusData)).catch(() => {});
    feedbackApi.stats().then((d) => setStats(d as FeedbackStats)).catch(() => {});
    profileApi
      .get()
      .then((d) => {
        const p = d as ProfileData;
        setProfileData({
          auto_apply_threshold: p.auto_apply_threshold ?? 85,
          suggest_threshold: p.suggest_threshold ?? 60,
          auto_schedule_threshold: p.auto_schedule_threshold ?? 90,
        });
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await profileApi.update(profileData as unknown as Record<string, unknown>);
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
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500">Agent configuration and integrations</p>
      </div>

      {/* Agent Status */}
      <section className="mb-8 rounded-lg border border-gray-800 bg-gray-900 p-5">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
          Agent Performance
        </h2>
        <div className="mb-4 grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-gray-500">Status</p>
            <div className="mt-1 flex items-center gap-2">
              <span
                className={`inline-block h-2.5 w-2.5 rounded-full ${
                  agentData?.status === "running"
                    ? "bg-green-500"
                    : "bg-yellow-500"
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
      </section>

      {/* Automation Thresholds */}
      <section className="mb-8 rounded-lg border border-gray-800 bg-gray-900 p-5">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
          Automation Thresholds
        </h2>
        <div className="space-y-5">
          <div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Auto-Apply Threshold</label>
              <span className="text-sm font-mono text-indigo-400">
                {profileData.auto_apply_threshold}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={profileData.auto_apply_threshold}
              onChange={(e) =>
                setProfileData({
                  ...profileData,
                  auto_apply_threshold: Number(e.target.value),
                })
              }
              className="mt-2 w-full accent-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-600">
              Events scoring above this are automatically applied to
            </p>
          </div>
          <div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Suggest Threshold</label>
              <span className="text-sm font-mono text-indigo-400">
                {profileData.suggest_threshold}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={profileData.suggest_threshold}
              onChange={(e) =>
                setProfileData({
                  ...profileData,
                  suggest_threshold: Number(e.target.value),
                })
              }
              className="mt-2 w-full accent-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-600">
              Events scoring above this are shown for review
            </p>
          </div>
          <div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Auto-Schedule Threshold</label>
              <span className="text-sm font-mono text-indigo-400">
                {profileData.auto_schedule_threshold}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={profileData.auto_schedule_threshold}
              onChange={(e) =>
                setProfileData({
                  ...profileData,
                  auto_schedule_threshold: Number(e.target.value),
                })
              }
              className="mt-2 w-full accent-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-600">
              Confirmed events scoring above this are auto-added to calendar
            </p>
          </div>
        </div>
        <div className="mt-5">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Thresholds"}
          </button>
        </div>
      </section>

      {/* Integrations */}
      <section className="rounded-lg border border-gray-800 bg-gray-900 p-5">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
          Integrations
        </h2>
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
      </section>
    </div>
  );
}
