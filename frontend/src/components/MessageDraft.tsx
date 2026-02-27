"use client";

import type { ColdMessage } from "@/lib/types";

const channelLabels: Record<string, string> = {
  twitter_dm: "Twitter DM",
  linkedin: "LinkedIn",
  email: "Email",
  instagram_dm: "Instagram DM",
};

const channelColors: Record<string, string> = {
  twitter_dm: "bg-blue-900 text-blue-300",
  linkedin: "bg-indigo-900 text-indigo-300",
  email: "bg-gray-700 text-gray-300",
  instagram_dm: "bg-pink-900 text-pink-300",
};

export default function MessageDraft({
  message,
  onApprove,
  onEdit,
  onSkip,
}: {
  message: ColdMessage;
  onApprove?: (id: string) => void;
  onEdit?: (id: string) => void;
  onSkip?: (id: string) => void;
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold text-gray-100">
            {message.recipient.name}
          </p>
          <p className="text-sm text-gray-500">
            {message.recipient.title}
            {message.recipient.title && message.recipient.company && " at "}
            {message.recipient.company}
          </p>
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            channelColors[message.channel] ?? "bg-gray-700 text-gray-300"
          }`}
        >
          {channelLabels[message.channel] ?? message.channel}
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-400">
        Re: {message.event.title}
      </p>
      <div className="mt-3 rounded bg-gray-950 p-3 text-sm leading-relaxed text-gray-300">
        {message.content}
      </div>
      <div className="mt-3 flex items-center gap-2">
        {onApprove && (
          <button
            onClick={() => onApprove(message.id)}
            className="rounded bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-500"
          >
            Send
          </button>
        )}
        {onEdit && (
          <button
            onClick={() => onEdit(message.id)}
            className="rounded bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-500"
          >
            Edit
          </button>
        )}
        {onSkip && (
          <button
            onClick={() => onSkip(message.id)}
            className="rounded bg-gray-700 px-3 py-1 text-xs font-medium text-gray-300 hover:bg-gray-600"
          >
            Skip
          </button>
        )}
      </div>
    </div>
  );
}
