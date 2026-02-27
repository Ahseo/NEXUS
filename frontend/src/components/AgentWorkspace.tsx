"use client";

import { useEffect, useState, useRef } from "react";

/* ─── Agent definitions ────────────────────────────── */

interface AgentDef {
  id: string;
  name: string;
  role: string;
  emoji: string;
  accent: string;
  accentBg: string;
  accentRing: string;
  accentText: string;
  tasks: string[];
}

const AGENTS: AgentDef[] = [
  {
    id: "scout",
    name: "Scout",
    role: "Event Discovery",
    emoji: "🔭",
    accent: "#6366f1",
    accentBg: "bg-indigo-50",
    accentRing: "ring-indigo-100",
    accentText: "text-indigo-600",
    tasks: [
      "Scanning Eventbrite SF...",
      "Found: AI Founders Mixer ✨",
      "Checking Luma calendar...",
      "Parsing meetup.com pages",
      "3 new events discovered!",
      "Scanning Twitter Spaces...",
      "Found: YC Demo Day 🎯",
      "Indexing Partiful invites",
    ],
  },
  {
    id: "analyst",
    name: "Analyst",
    role: "Score & Rank",
    emoji: "📊",
    accent: "#10b981",
    accentBg: "bg-emerald-50",
    accentRing: "ring-emerald-100",
    accentText: "text-emerald-600",
    tasks: [
      "Relevance score: 87/100",
      "Analyzing speaker lineup",
      "Cross-checking your goals",
      "Topic match: AI + SaaS ✓",
      "Score calculated: 92 🔥",
      "Ranking 12 events...",
      "Cost-benefit analysis...",
      "Top pick: Demo Day!",
    ],
  },
  {
    id: "nexus",
    name: "Nexus",
    role: "People Intel",
    emoji: "🕸️",
    accent: "#8b5cf6",
    accentBg: "bg-violet-50",
    accentRing: "ring-violet-100",
    accentText: "text-violet-600",
    tasks: [
      "Building social graph...",
      "Found 5 mutual friends!",
      "Researching attendees...",
      "Neo4j query complete ✓",
      "Mapping connections...",
      "LinkedIn deep scan...",
      "3 shared topics found",
      "Graph +8 new nodes 🌐",
    ],
  },
  {
    id: "scribe",
    name: "Scribe",
    role: "Message Craft",
    emoji: "✍️",
    accent: "#f59e0b",
    accentBg: "bg-amber-50",
    accentRing: "ring-amber-100",
    accentText: "text-amber-600",
    tasks: [
      "Drafting intro for Alex",
      "Personalizing message...",
      "Tone adjusted: casual 💬",
      "Adding shared context",
      "Message draft ready! ✉️",
      "Crafting follow-up...",
      "A/B testing openers...",
      "DM template polished ✨",
    ],
  },
];

/* ─── SVG Character Components ─────────────────────── */

function ScoutChar({ phase }: { phase: number }) {
  const eyeAnim = phase % 5 === 0 ? "agent-blink 0.3s ease" : "none";
  return (
    <svg viewBox="0 0 80 90" width="80" height="90" className="overflow-visible">
      {/* Body */}
      <ellipse cx="40" cy="72" rx="18" ry="14" fill="#c7d2fe" stroke="#6366f1" strokeWidth="1.5" />
      {/* Badge */}
      <circle cx="40" cy="70" r="4" fill="#6366f1" opacity="0.3" />
      {/* Left arm */}
      <g style={{ transformOrigin: "24px 65px", animation: "arm-scan 2s ease-in-out infinite" }}>
        <rect x="12" y="62" width="14" height="6" rx="3" fill="#a5b4fc" stroke="#6366f1" strokeWidth="1" />
      </g>
      {/* Right arm holding binoculars */}
      <g style={{ transformOrigin: "56px 65px", animation: "arm-scan 2s ease-in-out infinite 0.3s" }}>
        <rect x="54" y="62" width="14" height="6" rx="3" fill="#a5b4fc" stroke="#6366f1" strokeWidth="1" />
        <circle cx="72" cy="60" r="4" fill="#e0e7ff" stroke="#6366f1" strokeWidth="1" />
        <circle cx="72" cy="60" r="2" fill="#6366f1" opacity="0.4" />
      </g>
      {/* Head */}
      <circle cx="40" cy="40" r="20" fill="#e0e7ff" stroke="#6366f1" strokeWidth="1.5" />
      {/* Antenna */}
      <line x1="40" y1="20" x2="40" y2="12" stroke="#6366f1" strokeWidth="1.5" />
      <circle cx="40" cy="10" r="3" fill="#6366f1">
        <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
      </circle>
      {/* Radar ring */}
      <circle cx="40" cy="10" r="3" fill="none" stroke="#6366f1" strokeWidth="0.5"
        style={{ animation: "radar-ring 1.5s ease-out infinite" }} />
      {/* Eyes */}
      <g style={{ animation: eyeAnim }}>
        <g style={{ animation: "agent-look 4s ease-in-out infinite" }}>
          <ellipse cx="33" cy="38" rx="4" ry="4.5" fill="white" stroke="#6366f1" strokeWidth="1" />
          <circle cx="34" cy="38" r="2" fill="#312e81" />
          <circle cx="34.8" cy="37" r="0.8" fill="white" />
          <ellipse cx="47" cy="38" rx="4" ry="4.5" fill="white" stroke="#6366f1" strokeWidth="1" />
          <circle cx="48" cy="38" r="2" fill="#312e81" />
          <circle cx="48.8" cy="37" r="0.8" fill="white" />
        </g>
      </g>
      {/* Mouth - cute smile */}
      <path d="M35 47 Q40 51 45 47" fill="none" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" />
      {/* Cheeks */}
      <circle cx="27" cy="44" r="3" fill="#c7d2fe" style={{ animation: "cheek-pulse 3s ease-in-out infinite" }} />
      <circle cx="53" cy="44" r="3" fill="#c7d2fe" style={{ animation: "cheek-pulse 3s ease-in-out infinite 0.5s" }} />
      {/* Feet */}
      <ellipse cx="32" cy="85" rx="7" ry="4" fill="#a5b4fc" stroke="#6366f1" strokeWidth="1" />
      <ellipse cx="48" cy="85" rx="7" ry="4" fill="#a5b4fc" stroke="#6366f1" strokeWidth="1" />
    </svg>
  );
}

function AnalystChar({ phase }: { phase: number }) {
  const eyeAnim = phase % 4 === 0 ? "agent-blink 0.3s ease" : "none";
  return (
    <svg viewBox="0 0 80 90" width="80" height="90" className="overflow-visible">
      {/* Body */}
      <ellipse cx="40" cy="72" rx="18" ry="14" fill="#d1fae5" stroke="#10b981" strokeWidth="1.5" />
      <circle cx="40" cy="70" r="4" fill="#10b981" opacity="0.3" />
      {/* Left arm */}
      <g style={{ transformOrigin: "24px 65px", animation: "arm-type-l 1.2s ease-in-out infinite" }}>
        <rect x="12" y="62" width="14" height="6" rx="3" fill="#a7f3d0" stroke="#10b981" strokeWidth="1" />
      </g>
      {/* Right arm holding chart */}
      <g style={{ transformOrigin: "56px 65px", animation: "arm-type-r 1.2s ease-in-out infinite 0.15s" }}>
        <rect x="54" y="62" width="14" height="6" rx="3" fill="#a7f3d0" stroke="#10b981" strokeWidth="1" />
      </g>
      {/* Mini chart floating above */}
      <g transform="translate(58, 44)">
        {[0, 5, 10, 15].map((x, i) => (
          <rect key={i} x={x} y={0} width="3" rx="1" fill="#10b981" opacity="0.6"
            style={{
              height: "10px",
              transformOrigin: `${x + 1.5}px 10px`,
              animation: `bar-grow 1.8s ease-in-out infinite ${i * 0.25}s`,
            }}
          />
        ))}
      </g>
      {/* Head */}
      <circle cx="40" cy="40" r="20" fill="#ecfdf5" stroke="#10b981" strokeWidth="1.5" />
      {/* Glasses */}
      <rect x="26" y="34" width="12" height="10" rx="3" fill="none" stroke="#065f46" strokeWidth="1.2" />
      <rect x="42" y="34" width="12" height="10" rx="3" fill="none" stroke="#065f46" strokeWidth="1.2" />
      <line x1="38" y1="39" x2="42" y2="39" stroke="#065f46" strokeWidth="1" />
      <line x1="26" y1="39" x2="22" y2="37" stroke="#065f46" strokeWidth="1" />
      <line x1="54" y1="39" x2="58" y2="37" stroke="#065f46" strokeWidth="1" />
      {/* Eyes behind glasses */}
      <g style={{ animation: eyeAnim }}>
        <circle cx="32" cy="39" r="2" fill="#064e3b" />
        <circle cx="32.6" cy="38.2" r="0.7" fill="white" />
        <circle cx="48" cy="39" r="2" fill="#064e3b" />
        <circle cx="48.6" cy="38.2" r="0.7" fill="white" />
      </g>
      {/* Thinking mouth */}
      <circle cx="40" cy="49" r="2.5" fill="#d1fae5" stroke="#10b981" strokeWidth="1" />
      {/* Cheeks */}
      <circle cx="27" cy="45" r="3" fill="#a7f3d0" style={{ animation: "cheek-pulse 2.5s ease-in-out infinite" }} />
      <circle cx="53" cy="45" r="3" fill="#a7f3d0" style={{ animation: "cheek-pulse 2.5s ease-in-out infinite 0.3s" }} />
      {/* Hat / top */}
      <path d="M28 24 L40 14 L52 24" fill="#d1fae5" stroke="#10b981" strokeWidth="1.2" />
      {/* Feet */}
      <ellipse cx="32" cy="85" rx="7" ry="4" fill="#a7f3d0" stroke="#10b981" strokeWidth="1" />
      <ellipse cx="48" cy="85" rx="7" ry="4" fill="#a7f3d0" stroke="#10b981" strokeWidth="1" />
    </svg>
  );
}

function NexusChar({ phase }: { phase: number }) {
  const eyeAnim = phase % 6 === 0 ? "agent-blink 0.3s ease" : "none";
  return (
    <svg viewBox="0 0 80 90" width="80" height="90" className="overflow-visible">
      {/* Orbiting nodes */}
      {[0, 1, 2].map((i) => (
        <circle key={i} cx="40" cy="40" r="3" fill="#8b5cf6" opacity="0.7"
          style={{ animation: `node-orbit ${3 + i * 0.5}s linear infinite ${i * 1}s` }} />
      ))}
      {/* Body */}
      <ellipse cx="40" cy="72" rx="18" ry="14" fill="#ede9fe" stroke="#8b5cf6" strokeWidth="1.5" />
      <circle cx="40" cy="70" r="4" fill="#8b5cf6" opacity="0.2" />
      {/* Left arm - waving */}
      <g style={{ transformOrigin: "24px 65px", animation: "arm-wave 2.5s ease-in-out infinite" }}>
        <rect x="10" y="62" width="16" height="6" rx="3" fill="#ddd6fe" stroke="#8b5cf6" strokeWidth="1" />
        <circle cx="8" cy="65" r="3" fill="#ddd6fe" stroke="#8b5cf6" strokeWidth="1" />
      </g>
      {/* Right arm */}
      <g style={{ transformOrigin: "56px 65px", animation: "arm-wave 2.5s ease-in-out infinite 1.2s" }}>
        <rect x="54" y="62" width="16" height="6" rx="3" fill="#ddd6fe" stroke="#8b5cf6" strokeWidth="1" />
        <circle cx="72" cy="65" r="3" fill="#ddd6fe" stroke="#8b5cf6" strokeWidth="1" />
      </g>
      {/* Head */}
      <circle cx="40" cy="40" r="20" fill="#f5f3ff" stroke="#8b5cf6" strokeWidth="1.5" />
      {/* Ears / antennas */}
      <circle cx="22" cy="32" r="4" fill="#ede9fe" stroke="#8b5cf6" strokeWidth="1" />
      <circle cx="58" cy="32" r="4" fill="#ede9fe" stroke="#8b5cf6" strokeWidth="1" />
      <circle cx="22" cy="32" r="1.5" fill="#8b5cf6" opacity="0.4" />
      <circle cx="58" cy="32" r="1.5" fill="#8b5cf6" opacity="0.4" />
      {/* Eyes - big sparkly */}
      <g style={{ animation: eyeAnim }}>
        <g style={{ animation: "agent-look 5s ease-in-out infinite" }}>
          <ellipse cx="33" cy="38" rx="5" ry="5.5" fill="white" stroke="#8b5cf6" strokeWidth="1" />
          <circle cx="34" cy="38" r="2.5" fill="#4c1d95" />
          <circle cx="35" cy="36.5" r="1" fill="white" />
          <circle cx="33.5" cy="39" r="0.5" fill="white" />
          <ellipse cx="47" cy="38" rx="5" ry="5.5" fill="white" stroke="#8b5cf6" strokeWidth="1" />
          <circle cx="48" cy="38" r="2.5" fill="#4c1d95" />
          <circle cx="49" cy="36.5" r="1" fill="white" />
          <circle cx="47.5" cy="39" r="0.5" fill="white" />
        </g>
      </g>
      {/* Happy mouth */}
      <path d="M34 48 Q40 53 46 48" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" />
      {/* Cheeks */}
      <circle cx="26" cy="44" r="3.5" fill="#ddd6fe" style={{ animation: "cheek-pulse 2s ease-in-out infinite" }} />
      <circle cx="54" cy="44" r="3.5" fill="#ddd6fe" style={{ animation: "cheek-pulse 2s ease-in-out infinite 0.4s" }} />
      {/* Feet */}
      <ellipse cx="32" cy="85" rx="7" ry="4" fill="#ddd6fe" stroke="#8b5cf6" strokeWidth="1" />
      <ellipse cx="48" cy="85" rx="7" ry="4" fill="#ddd6fe" stroke="#8b5cf6" strokeWidth="1" />
    </svg>
  );
}

function ScribeChar({ phase }: { phase: number }) {
  const eyeAnim = phase % 3 === 0 ? "agent-blink 0.3s ease" : "none";
  return (
    <svg viewBox="0 0 80 90" width="80" height="90" className="overflow-visible">
      {/* Floating messages */}
      {[0, 1].map((i) => (
        <g key={i} style={{ animation: `msg-float 3s ease-out infinite ${i * 1.8}s` }}>
          <rect x={56 + i * 8} y={20 + i * 12} width="12" height="8" rx="3" fill="#fef3c7" stroke="#f59e0b" strokeWidth="0.8" />
          <line x1={58 + i * 8} y1={23 + i * 12} x2={66 + i * 8} y2={23 + i * 12} stroke="#f59e0b" strokeWidth="0.5" opacity="0.5" />
          <line x1={58 + i * 8} y1={25.5 + i * 12} x2={64 + i * 8} y2={25.5 + i * 12} stroke="#f59e0b" strokeWidth="0.5" opacity="0.3" />
        </g>
      ))}
      {/* Body */}
      <ellipse cx="40" cy="72" rx="18" ry="14" fill="#fef3c7" stroke="#f59e0b" strokeWidth="1.5" />
      <circle cx="40" cy="70" r="4" fill="#f59e0b" opacity="0.2" />
      {/* Left arm - typing */}
      <g style={{ transformOrigin: "24px 65px", animation: "arm-type-l 0.5s ease-in-out infinite" }}>
        <rect x="12" y="62" width="14" height="6" rx="3" fill="#fde68a" stroke="#f59e0b" strokeWidth="1" />
      </g>
      {/* Right arm - typing */}
      <g style={{ transformOrigin: "56px 65px", animation: "arm-type-r 0.5s ease-in-out infinite 0.1s" }}>
        <rect x="54" y="62" width="14" height="6" rx="3" fill="#fde68a" stroke="#f59e0b" strokeWidth="1" />
      </g>
      {/* Laptop */}
      <rect x="22" y="78" width="36" height="3" rx="1" fill="#d1d5db" stroke="#9ca3af" strokeWidth="0.5" />
      <rect x="26" y="73" width="28" height="6" rx="1" fill="#e5e7eb" stroke="#9ca3af" strokeWidth="0.5" />
      <rect x="29" y="74.5" width="8" height="0.8" rx="0.4" fill="#f59e0b" opacity="0.4" />
      <rect x="29" y="76.5" width="12" height="0.8" rx="0.4" fill="#f59e0b" opacity="0.2" />
      {/* Head */}
      <circle cx="40" cy="40" r="20" fill="#fffbeb" stroke="#f59e0b" strokeWidth="1.5" />
      {/* Beret */}
      <ellipse cx="42" cy="22" rx="14" ry="6" fill="#fde68a" stroke="#f59e0b" strokeWidth="1" />
      <circle cx="42" cy="18" r="2" fill="#f59e0b" />
      {/* Eyes - focused */}
      <g style={{ animation: eyeAnim }}>
        <ellipse cx="33" cy="38" rx="4" ry="4.5" fill="white" stroke="#f59e0b" strokeWidth="1" />
        <circle cx="34" cy="38" r="2" fill="#78350f" />
        <circle cx="34.8" cy="37" r="0.8" fill="white" />
        <ellipse cx="47" cy="38" rx="4" ry="4.5" fill="white" stroke="#f59e0b" strokeWidth="1" />
        <circle cx="48" cy="38" r="2" fill="#78350f" />
        <circle cx="48.8" cy="37" r="0.8" fill="white" />
      </g>
      {/* Concentrated mouth - small */}
      <ellipse cx="40" cy="48" rx="3" ry="2" fill="#fde68a" stroke="#f59e0b" strokeWidth="1" />
      {/* Cheeks */}
      <circle cx="26" cy="44" r="3" fill="#fde68a" style={{ animation: "cheek-pulse 2s ease-in-out infinite" }} />
      <circle cx="54" cy="44" r="3" fill="#fde68a" style={{ animation: "cheek-pulse 2s ease-in-out infinite 0.5s" }} />
      {/* Feet */}
      <ellipse cx="32" cy="85" rx="7" ry="4" fill="#fde68a" stroke="#f59e0b" strokeWidth="1" />
      <ellipse cx="48" cy="85" rx="7" ry="4" fill="#fde68a" stroke="#f59e0b" strokeWidth="1" />
    </svg>
  );
}

const CHAR_MAP: Record<string, React.FC<{ phase: number }>> = {
  scout: ScoutChar,
  analyst: AnalystChar,
  nexus: NexusChar,
  scribe: ScribeChar,
};

/* ─── Agent Card ───────────────────────────────────── */

function AgentCard({ agent, taskIndex }: { agent: AgentDef; taskIndex: number }) {
  const CharComponent = CHAR_MAP[agent.id];
  const task = agent.tasks[taskIndex % agent.tasks.length];
  const progress = ((taskIndex % agent.tasks.length) / agent.tasks.length) * 100;

  return (
    <div className="group flex flex-col items-center rounded-2xl border border-black/[0.04] bg-white p-4 pb-3 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)] hover:-translate-y-1">
      {/* Character with bounce */}
      <div
        className="relative mb-2"
        style={{
          animation: `agent-bounce 3s ease-in-out infinite`,
          animationDelay: `${AGENTS.indexOf(agent) * 0.4}s`,
        }}
      >
        {/* Glow under character */}
        <div
          className="absolute bottom-0 left-1/2 h-3 w-12 -translate-x-1/2 rounded-full blur-md"
          style={{ background: agent.accent, opacity: 0.15 }}
        />
        <CharComponent phase={taskIndex} />
      </div>

      {/* Name + role */}
      <div className="mb-2 text-center">
        <p className={`text-[13px] font-bold ${agent.accentText}`}>
          {agent.emoji} {agent.name}
        </p>
        <p className="text-[10px] text-gray-400">{agent.role}</p>
      </div>

      {/* Task bubble */}
      <div
        key={taskIndex}
        className={`w-full rounded-xl ${agent.accentBg} px-3 py-2 ring-1 ${agent.accentRing}`}
        style={{ animation: "bubble-pop 0.3s cubic-bezier(0.16,1,0.3,1)" }}
      >
        <p className="text-[11px] font-medium text-gray-600 truncate">{task}</p>
        {/* Tiny progress bar */}
        <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-black/[0.04]">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${progress}%`, background: agent.accent, opacity: 0.6 }}
          />
        </div>
      </div>
    </div>
  );
}

/* ─── Activity Log ─────────────────────────────────── */

interface LogEntry {
  id: number;
  agent: AgentDef;
  message: string;
  time: string;
}

function ActivityFeed({ logs }: { logs: LogEntry[] }) {
  if (logs.length === 0) return null;
  return (
    <div className="mt-4 rounded-2xl border border-black/[0.04] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <div className="mb-2.5 flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-orange-500" />
        </span>
        <span className="text-[11px] font-semibold uppercase tracking-widest text-gray-400">
          Live Activity
        </span>
      </div>
      <div className="space-y-1.5">
        {logs.map((log) => (
          <div
            key={log.id}
            className="flex items-center gap-2 text-[12px]"
            style={{ animation: "log-enter 0.3s ease-out" }}
          >
            <span className="shrink-0 text-gray-300 font-mono text-[10px]">{log.time}</span>
            <span
              className="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold text-white"
              style={{ background: log.agent.accent }}
            >
              {log.agent.name}
            </span>
            <span className="truncate text-gray-500">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Main Component ───────────────────────────────── */

export default function AgentWorkspace() {
  const [taskIndices, setTaskIndices] = useState([0, 0, 0, 0]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logId = useRef(0);
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setUptime((p) => p + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const intervals = AGENTS.map((_, idx) => {
      const delay = 2500 + idx * 800;
      return setInterval(() => {
        setTaskIndices((prev) => {
          const next = [...prev];
          const ni = prev[idx] + 1;
          next[idx] = ni;

          const a = AGENTS[idx];
          const now = new Date();
          const time = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;
          setLogs((p) => [{ id: logId.current++, agent: a, message: a.tasks[ni % a.tasks.length], time }, ...p].slice(0, 5));
          return next;
        });
      }, delay);
    });
    return () => intervals.forEach(clearInterval);
  }, []);

  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  return (
    <div className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#1a1a1a] text-[14px]">
            🤖
          </div>
          <div>
            <h2 className="text-[14px] font-bold text-gray-900">Agent Command Center</h2>
            <p className="text-[11px] text-gray-400">4 agents working · uptime {fmt(uptime)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {AGENTS.map((a) => (
            <div
              key={a.id}
              className="h-2 w-2 rounded-full animate-pulse"
              style={{ background: a.accent }}
              title={a.name}
            />
          ))}
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-4 gap-3 stagger-children">
        {AGENTS.map((agent, idx) => (
          <AgentCard key={agent.id} agent={agent} taskIndex={taskIndices[idx]} />
        ))}
      </div>

      {/* Live Activity Feed */}
      <ActivityFeed logs={logs} />
    </div>
  );
}
