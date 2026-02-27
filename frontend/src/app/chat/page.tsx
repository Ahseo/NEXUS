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

  useEffect(() => {
    chat
      .history()
      .then((data) => setMessages(data as Message[]))
      .catch(() => {});
  }, []);

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

              setMessages((prev) => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                const last = updated[lastIdx];

                if (last?.role === "assistant" && !last.content) {
                  updated.splice(lastIdx, 0, {
                    role: "tool",
                    content: `Searching: ${query || toolName}`,
                  });
                } else {
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
      <div className="flex items-center justify-between border-b border-black/[0.04] px-6 py-4">
        <div>
          <h1 className="text-[15px] font-semibold text-gray-900">Chat</h1>
          <p className="text-[12px] text-gray-400">
            Ask me to find events, research people, or draft messages
          </p>
        </div>
        <button
          onClick={() => {
            chat.clear();
            setMessages([]);
          }}
          className="flex items-center gap-1.5 rounded-xl border border-black/[0.06] px-3 py-1.5 text-[12px] font-medium text-gray-500 transition-all duration-200 hover:bg-white hover:shadow-sm hover:text-gray-700 active:scale-[0.97]"
        >
          <span className="text-sm leading-none">+</span>
          New
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center animate-fade-in">
            <div className="mb-5 flex h-16 w-16 items-center justify-center animate-float opacity-20">
              <img src="/logo.svg" alt="NEXUS" className="h-12 w-auto" />
            </div>
            <p className="text-sm text-gray-400">
              Start a conversation with your agent
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-2 stagger-children">
              {[
                "Find AI events in SF this week",
                "Who should I meet at the next meetup?",
                "Draft a message to a VC partner",
                "What events match my interests?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="rounded-full border border-black/[0.06] bg-white px-3.5 py-2 text-[12px] text-gray-500 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 hover:text-gray-700 active:scale-[0.97]"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          {messages.map((msg, i) => {
            if (msg.role === "tool") {
              return (
                <div key={i} className="flex justify-start animate-fade-in">
                  <div className="flex items-center gap-2 rounded-xl bg-orange-50 px-3 py-1.5 text-[12px] text-orange-600">
                    <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-orange-500" />
                    {msg.content}
                  </div>
                </div>
              );
            }

            return (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in-up`}
              >
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-[#1a1a1a] text-white"
                      : "bg-white text-gray-700 shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-black/[0.04]"
                  }`}
                >
                  {msg.content}
                  {msg.role === "assistant" && !msg.content && streaming && (
                    <span className="inline-flex items-center gap-1 text-gray-400">
                      <span className="inline-block h-1 w-1 animate-pulse rounded-full bg-gray-300" style={{ animationDelay: "0ms" }} />
                      <span className="inline-block h-1 w-1 animate-pulse rounded-full bg-gray-300" style={{ animationDelay: "150ms" }} />
                      <span className="inline-block h-1 w-1 animate-pulse rounded-full bg-gray-300" style={{ animationDelay: "300ms" }} />
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
      <div className="border-t border-black/[0.04] px-6 py-4">
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
            placeholder="Ask anything..."
            disabled={streaming}
            className="flex-1 rounded-xl border border-black/[0.06] bg-white px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 shadow-sm transition-all duration-200 focus:border-black/10 focus:outline-none focus:ring-2 focus:ring-black/[0.04] focus:shadow-md disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="rounded-xl bg-[#1a1a1a] px-5 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-[#333] active:scale-[0.97] disabled:opacity-30"
          >
            {streaming ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
