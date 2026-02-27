"use client";

import type { Person } from "@/lib/types";

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-green-900 text-green-300"
      : score >= 50
        ? "bg-yellow-900 text-yellow-300"
        : "bg-red-900 text-red-300";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
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
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold text-gray-100">{person.name}</p>
          {(person.title || person.company) && (
            <p className="text-sm text-gray-400">
              {person.title}
              {person.title && person.company && " at "}
              {person.company}
            </p>
          )}
        </div>
        <ScoreBadge score={person.connection_score} />
      </div>
      {reason && (
        <p className="mt-2 text-sm text-gray-500">{reason}</p>
      )}
      {person.shared_topics.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {person.shared_topics.map((t) => (
            <span
              key={t}
              className="rounded bg-gray-800 px-2 py-0.5 text-[10px] text-gray-400"
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
            className="text-xs text-indigo-400 hover:text-indigo-300"
          >
            LinkedIn
          </a>
        )}
        {person.twitter && (
          <a
            href={`https://twitter.com/${person.twitter.replace("@", "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-indigo-400 hover:text-indigo-300"
          >
            Twitter
          </a>
        )}
      </div>
    </div>
  );
}
