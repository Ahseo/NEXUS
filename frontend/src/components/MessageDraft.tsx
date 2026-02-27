"use client";

import type { ColdMessage } from "@/lib/types";

const channelLabels: Record<string, string> = {
  twitter_dm: "Twitter DM",
  linkedin: "LinkedIn",
  email: "Email",
  instagram_dm: "Instagram DM",
};

const channelColors: Record<string, string> = {
  twitter_dm: "bg-blue-50 text-blue-600",
  linkedin: "bg-blue-50 text-blue-700",
  email: "bg-[#F7F7F4] text-gray-500",
  instagram_dm: "bg-pink-50 text-pink-600",
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
    <div className="rounded-2xl border border-black/[0.04] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-[14px] text-gray-900">
            {message.recipient.name}
          </p>
          <p className="text-[12px] text-gray-400 truncate">
            {message.recipient.title}
            {message.recipient.title && message.recipient.company && " at "}
            {message.recipient.company}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-medium ${
            channelColors[message.channel] ?? "bg-[#F7F7F4] text-gray-500"
          }`}
        >
          {channelLabels[message.channel] ?? message.channel}
        </span>
      </div>
      <p className="mt-2 text-[12px] text-gray-400">
        Re: {message.event.title}
      </p>
      <div className="mt-3 rounded-xl bg-[#F7F7F4] p-3.5 text-[13px] leading-relaxed text-gray-600">
        {message.content}
      </div>
      {(onApprove || onEdit || onSkip) && (
        <div className="mt-3 flex items-center gap-2">
          {onApprove && (
            <button
              onClick={() => onApprove(message.id)}
              className="rounded-xl bg-[#1a1a1a] px-3.5 py-1.5 text-[12px] font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97]"
            >
              Send
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(message.id)}
              className="rounded-xl border border-black/[0.06] bg-white px-3.5 py-1.5 text-[12px] font-medium text-gray-500 transition-all duration-200 hover:bg-gray-50 active:scale-[0.97]"
            >
              Edit
            </button>
          )}
          {onSkip && (
            <button
              onClick={() => onSkip(message.id)}
              className="rounded-xl px-3.5 py-1.5 text-[12px] font-medium text-gray-400 transition-all duration-200 hover:bg-black/[0.04] hover:text-gray-600 active:scale-[0.97]"
            >
              Skip
            </button>
          )}
        </div>
      )}
    </div>
  );
}
