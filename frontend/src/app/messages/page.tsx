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
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100">Messages</h1>
        <p className="text-sm text-gray-500">
          Review and approve draft messages before they are sent
        </p>
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center text-gray-500">
          Loading messages...
        </div>
      ) : (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-500">
              <span className="inline-block h-2 w-2 rounded-full bg-yellow-500" />
              Pending Approval ({drafts.length})
            </h2>
            {drafts.length === 0 ? (
              <p className="text-sm text-gray-600">No drafts to review.</p>
            ) : (
              <div className="space-y-3">
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

          <section>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-500">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              Sent ({sent.length})
            </h2>
            {sent.length === 0 ? (
              <p className="text-sm text-gray-600">No messages sent yet.</p>
            ) : (
              <div className="space-y-3">
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
