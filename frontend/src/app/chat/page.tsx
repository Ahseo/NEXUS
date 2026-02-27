"use client";

import { useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";

interface Message {
  role: "user" | "assistant" | "tool";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load history on mount
  useEffect(() => {
    chat
      .history()
      .then((data) => setMessages(data as Message[]))
      .catch(() => {});
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTool]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || streaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setStreaming(true);
    setActiveTool(null);

    // Add empty assistant message to fill in
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const res = await chat.send(text);
      if (!res.body) return;

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6));

            if (payload.type === "text") {
              setActiveTool(null);
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === "assistant") {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + payload.content,
                  };
                }
                return updated;
              });
            } else if (payload.type === "tool_use") {
              const toolName = payload.tool as string;
              const query = payload.input?.query || "";
              setActiveTool(toolName);

              // Show tool usage in chat as a special message
              setMessages((prev) => {
                // Insert a tool message before the last assistant message
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                const last = updated[lastIdx];

                // Only insert tool msg if the last assistant msg is still empty
                if (last?.role === "assistant" && !last.content) {
                  updated.splice(lastIdx, 0, {
                    role: "tool",
                    content: `Searching: ${query || toolName}`,
                  });
                } else {
                  // Append after the current assistant message and add a new empty one
                  updated.push({
                    role: "tool",
                    content: `Searching: ${query || toolName}`,
                  });
                  updated.push({ role: "assistant", content: "" });
                }
                return updated;
              });
            } else if (payload.type === "done") {
              setActiveTool(null);
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && !last.content) {
          updated[updated.length - 1] = {
            ...last,
            content: "Failed to get response. Please try again.",
          };
        }
        return updated;
      });
    } finally {
      setStreaming(false);
      setActiveTool(null);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold text-gray-100">NEXUS Agent</h1>
          <p className="text-xs text-gray-500">
            Ask me to find events, research people, or draft messages
          </p>
        </div>
        <button
          onClick={() => {
            chat.clear();
            setMessages([]);
          }}
          className="flex items-center gap-1.5 rounded-lg border border-gray-700 px-3 py-1.5 text-xs font-medium text-gray-300 transition hover:border-indigo-500 hover:text-indigo-400"
        >
          <span className="text-sm leading-none">+</span>
          New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 text-4xl text-indigo-400/30">N</div>
            <p className="text-sm text-gray-500">
              Start a conversation with your networking agent
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                "Find AI events in SF this week",
                "Who should I meet at the next meetup?",
                "Draft a message to a VC partner",
                "What events match my interests?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                  }}
                  className="rounded-full border border-gray-800 px-3 py-1.5 text-xs text-gray-400 transition hover:border-indigo-500/50 hover:text-gray-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-4">
          {messages.map((msg, i) => {
            // Tool usage indicator
            if (msg.role === "tool") {
              return (
                <div key={i} className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-3 py-1.5 text-xs text-indigo-300">
                    <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-400" />
                    {msg.content}
                  </div>
                </div>
              );
            }

            return (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[75%] rounded-lg px-4 py-2.5 text-sm whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-800 text-gray-200"
                  }`}
                >
                  {msg.content}
                  {msg.role === "assistant" && !msg.content && streaming && (
                    <span className="inline-block animate-pulse text-gray-500">
                      {activeTool ? `Using ${activeTool}...` : "Thinking..."}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 px-6 py-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask NEXUS anything..."
            disabled={streaming}
            className="flex-1 rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:opacity-50"
          >
            {streaming ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
