"use client";

import type { Person } from "@/lib/types";

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-orange-50 text-orange-600"
      : score >= 50
        ? "bg-[#F7F7F4] text-gray-600"
        : "bg-[#F7F7F4] text-gray-400";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold tabular-nums ${color}`}>
      {score}
    </span>
  );
}

export default function PersonCard({
  person,
  reason,
}: {
  person: Person;
  reason?: string;
}) {
  return (
    <div className="group rounded-2xl border border-black/[0.04] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-[14px] text-gray-900">{person.name}</p>
          {(person.title || person.company) && (
            <p className="text-[12px] text-gray-400 truncate">
              {person.title}
              {person.title && person.company && " at "}
              {person.company}
            </p>
          )}
        </div>
        <ScoreBadge score={person.connection_score} />
      </div>
      {reason && (
        <p className="mt-2 text-[12px] text-gray-500">{reason}</p>
      )}
      {person.shared_topics.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {person.shared_topics.map((t) => (
            <span
              key={t}
              className="rounded-full bg-[#F7F7F4] px-2 py-0.5 text-[10px] font-medium text-gray-500"
            >
              {t}
            </span>
          ))}
        </div>
      )}
      <div className="mt-3 flex items-center gap-3">
        {person.linkedin && (
          <a
            href={person.linkedin}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] font-medium text-gray-400 transition-colors hover:text-gray-700"
          >
            LinkedIn
          </a>
        )}
        {person.twitter && (
          <a
            href={`https://twitter.com/${person.twitter.replace("@", "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] font-medium text-gray-400 transition-colors hover:text-gray-700"
          >
            Twitter
          </a>
        )}
      </div>
    </div>
  );
}
