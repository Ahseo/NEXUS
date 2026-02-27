"use client";

import { useEffect, useState } from "react";
import { messages as messagesApi } from "@/lib/api";
import type { ColdMessage } from "@/lib/types";
import MessageDraft from "@/components/MessageDraft";

export default function MessagesPage() {
  const [messageList, setMessageList] = useState<ColdMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    messagesApi
      .list()
      .then((data) => setMessageList(data as ColdMessage[]))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await messagesApi.approve(id);
      setMessageList((prev) =>
        prev.map((m) => (m.id === id ? { ...m, status: "approved" } : m))
      );
    } catch {
      /* ignore */
    }
  };

  const handleEdit = (id: string) => {
    const msg = messageList.find((m) => m.id === id);
    if (!msg) return;
    const newContent = window.prompt("Edit message:", msg.content);
    if (newContent && newContent !== msg.content) {
      messagesApi
        .edit(id, newContent)
        .then(() => {
          setMessageList((prev) =>
            prev.map((m) =>
              m.id === id ? { ...m, content: newContent, status: "edited" } : m
            )
          );
        })
        .catch(() => {});
    }
  };

  const handleSkip = async (id: string) => {
    try {
      await messagesApi.reject(id);
      setMessageList((prev) =>
        prev.map((m) => (m.id === id ? { ...m, status: "rejected" } : m))
      );
    } catch {
      /* ignore */
    }
  };

  const drafts = messageList.filter(
    (m) => m.status === "draft" || m.status === "edited"
  );
  const sent = messageList.filter((m) => m.status === "sent" || m.status === "approved");

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
        <p className="text-[13px] text-gray-400">
          Review and approve draft messages before they are sent
        </p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-32 rounded-2xl bg-white/60 animate-pulse"
              style={{ animationDelay: `${n * 80}ms` }}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          {/* Pending Drafts */}
          <section className="animate-fade-in-up">
            <h2 className="mb-3 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wider text-gray-400">
              <span className="inline-block h-2 w-2 rounded-full bg-orange-400" />
              Pending Approval ({drafts.length})
            </h2>
            {drafts.length === 0 ? (
              <p className="text-[13px] text-gray-400">No drafts to review.</p>
            ) : (
              <div className="space-y-3 stagger-children">
                {drafts.map((msg) => (
                  <MessageDraft
                    key={msg.id}
                    message={msg}
                    onApprove={handleApprove}
                    onEdit={handleEdit}
                    onSkip={handleSkip}
                  />
                ))}
              </div>
            )}
          </section>

          {/* Sent */}
          <section className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
            <h2 className="mb-3 flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wider text-gray-400">
              <span className="inline-block h-2 w-2 rounded-full bg-gray-400" />
              Sent ({sent.length})
            </h2>
            {sent.length === 0 ? (
              <p className="text-[13px] text-gray-400">No messages sent yet.</p>
            ) : (
              <div className="space-y-3 stagger-children">
                {sent.map((msg) => (
                  <MessageDraft key={msg.id} message={msg} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
