"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Send, Sparkles, User, Bot, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "ai";
  content: string;
  results?: any[];
}

export default function AskPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", content: "Hi! I'm the Kovi AI assistant. Ask me anything about your customers, opportunities, or identity matches.\n\nTry: \"Show me HNI customers in Mumbai without Insurance\"" }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const res = await api.post("/ai/nl-query", { query: userMsg });
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: res.data.explanation || res.data.answer || JSON.stringify(res.data, null, 2),
        results: res.data.results 
      }]);
    } catch {
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: "I couldn't process that query right now. Try rephrasing or check if the AI service is configured." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full gap-6">
      <div className="bg-white p-6 rounded-3xl card-shadow">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
            <Sparkles size={20} className="text-indigo-600" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">Ask Kovi</h2>
            <p className="text-gray-500 text-sm mt-0.5">Natural language queries powered by AI</p>
          </div>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 bg-white rounded-3xl card-shadow p-6 overflow-y-auto flex flex-col gap-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
              msg.role === "user" ? "bg-[#E2604B] text-white" : "bg-indigo-100 text-indigo-600"
            }`}>
              {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className={`max-w-[70%] rounded-2xl p-4 text-sm ${
              msg.role === "user" 
                ? "bg-[#E2604B] text-white rounded-tr-none" 
                : "bg-gray-50 text-gray-800 rounded-tl-none border border-gray-100"
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.results && msg.results.length > 0 && (
                <div className="mt-3 border-t border-gray-200 pt-3">
                  <p className="text-xs font-semibold text-gray-500 mb-2">{msg.results.length} results found:</p>
                  <div className="space-y-2">
                    {msg.results.slice(0, 5).map((r: any, idx: number) => (
                      <div key={idx} className="bg-white rounded-lg p-2 text-xs border border-gray-100">
                        <span className="font-semibold">{r.name || r.canonical_name || `Record #${r.id}`}</span>
                        {r.city && <span className="text-gray-500 ml-2">· {r.city}</span>}
                        {r.segment && <span className="text-gray-500 ml-2">· {r.segment}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0">
              <Bot size={14} />
            </div>
            <div className="bg-gray-50 rounded-2xl rounded-tl-none p-4 border border-gray-100">
              <Loader2 size={16} className="animate-spin text-indigo-500" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="bg-white rounded-3xl card-shadow p-3 flex items-center gap-3">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask anything about your customers..."
          className="flex-1 px-4 py-3 bg-gray-50 rounded-2xl text-sm focus:ring-2 focus:ring-indigo-300 border-none"
        />
        <button 
          type="submit"
          disabled={isLoading || !input.trim()}
          className="w-12 h-12 rounded-xl bg-[#E2604B] text-white flex items-center justify-center hover:bg-orange-600 transition-colors disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
