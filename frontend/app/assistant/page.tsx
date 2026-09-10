"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import {
  Bot,
  User as UserIcon,
  Send,
  Sparkles,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  ArrowRight
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "agent";
  text: string;
  toolsExecuted?: any[];
  requiresClarification?: boolean;
  suggestedCategories?: string[];
  pendingTransaction?: any;
  createdAlert?: any;
  createdExpense?: any;
  timestamp: string;
}

const QUICK_PROMPTS = [
  "I spent ₹4,500 at a restaurant.",
  "Paid ₹2,500 to Rahul",
  "Am I spending too much on food?",
  "Find unusual expenses.",
  "Create a ₹5,000 entertainment budget.",
  "Generate my monthly spending report."
];

function AssistantContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q");

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "agent",
      text: "Hello! I am **FinAgent**, your autonomous financial intelligence orchestrator. I can log expenses, track category velocity, evaluate 3-layer anomaly risks, and monitor your monthly budgets. How can I help you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

  useEffect(() => {
    if (initialQuery) {
      sendMessage(initialQuery);
    }
  }, [initialQuery]);

  const toggleTools = (msgId: string) => {
    setExpandedTools((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const sendMessage = async (userText: string) => {
    if (!userText.trim() || isProcessing) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsProcessing(true);

    try {
      const res = await api.chat(userText);

      const agentMsg: Message = {
        id: `agent-${Date.now()}`,
        sender: "agent",
        text: res.response,
        toolsExecuted: res.tools_executed || [],
        requiresClarification: res.requires_clarification,
        suggestedCategories: res.suggested_categories || [],
        pendingTransaction: res.pending_transaction,
        createdAlert: res.created_alert,
        createdExpense: res.created_expense,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, agentMsg]);

      // Automatically expand tools if any executed
      if (res.tools_executed && res.tools_executed.length > 0) {
        setExpandedTools((prev) => ({ ...prev, [agentMsg.id]: true }));
      }
    } catch (err: any) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        sender: "agent",
        text: `Sorry, I encountered an issue: ${err.message || "Failed to communicate with agent."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClarificationChoice = (choice: string) => {
    sendMessage(`The category was ${choice}.`);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] glass-panel rounded-2xl border border-slate-800 overflow-hidden animate-in fade-in duration-300">
      {/* Chat Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-400 p-0.5 shadow-md shadow-indigo-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Bot className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-tight">FinAgent Orchestrator</h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                LangGraph Active
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Autonomous Reasoning & Tool Execution</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-[11px] text-slate-400 hidden sm:block">
            Confidence threshold: <span className="text-indigo-300 font-semibold">75%</span>
          </div>
          <button
            onClick={() => {
              setMessages([
                {
                  id: "welcome",
                  sender: "agent",
                  text: "Hello! I am **FinAgent**, your autonomous financial intelligence orchestrator. How can I assist with your expenses or budgets today?",
                  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                },
              ]);
            }}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-[11px] transition-colors"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-5">
        {messages.map((m) => {
          const isAgent = m.sender === "agent";
          const isToolsOpen = expandedTools[m.id] ?? false;

          return (
            <div
              key={m.id}
              className={`flex items-start gap-3 max-w-3xl ${isAgent ? "" : "ml-auto flex-row-reverse"}`}
            >
              <div
                className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center text-xs font-bold ${
                  isAgent
                    ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                    : "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30"
                }`}
              >
                {isAgent ? <Bot className="w-4 h-4" /> : <UserIcon className="w-4 h-4" />}
              </div>

              <div className="space-y-2 max-w-xl">
                {/* Tool Traces Chip (Compact Expandable) */}
                {isAgent && m.toolsExecuted && m.toolsExecuted.length > 0 && (
                  <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden text-xs">
                    <button
                      onClick={() => toggleTools(m.id)}
                      className="w-full px-3 py-2 flex items-center justify-between text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 transition-colors"
                    >
                      <span className="flex items-center gap-2 font-medium text-[11px]">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                        Executed {m.toolsExecuted.length} autonomous tools
                      </span>
                      {isToolsOpen ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {isToolsOpen && (
                      <div className="p-3 border-t border-slate-800 space-y-1.5 bg-slate-950/40">
                        {m.toolsExecuted.map((t: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between text-[11px]">
                            <div className="flex items-center gap-2">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                              <span className="font-mono text-indigo-300">{t.tool_name}</span>
                            </div>
                            <span className="text-slate-500 font-mono text-[10px]">
                              {JSON.stringify(t.arguments || {}).slice(0, 30)}...
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`p-4 rounded-2xl text-xs md:text-sm leading-relaxed ${
                    isAgent
                      ? "bg-slate-900/90 border border-slate-800 text-slate-100 shadow-sm"
                      : "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  }`}
                >
                  <div className="whitespace-pre-line font-normal">{m.text}</div>

                  {/* Clarification Quick Choice Chips */}
                  {m.requiresClarification && m.suggestedCategories && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80">
                      <span className="text-[11px] font-semibold text-amber-300 block mb-2 flex items-center gap-1">
                        <HelpCircle className="w-3 h-3" /> Select or specify category:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {m.suggestedCategories.map((cat) => (
                          <button
                            key={cat}
                            onClick={() => handleClarificationChoice(cat)}
                            className="px-2.5 py-1 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-all"
                          >
                            {cat}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Created Alert preview banner */}
                  {m.createdAlert && (
                    <div className="mt-3 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300">
                      <b>Proactive Alert Logged</b>: {m.createdAlert.title}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between px-1 text-[10px] text-slate-500">
                  <span>{m.timestamp}</span>
                  {isAgent && (
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(m.text);
                      }}
                      className="text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      Copy
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex items-start gap-3 max-w-xl animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
              <span>FinAgent reasoning & evaluating tools...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Carousel */}
      <div className="px-4 py-2 bg-slate-950/70 border-t border-slate-800/80 flex items-center gap-2 overflow-x-auto">
        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider shrink-0">
          Try Asking:
        </span>
        {QUICK_PROMPTS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(p)}
            className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 hover:text-white transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type an expense (e.g. ₹4,500 at restaurant) or ask questions..."
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/30"
          />
          <button
            type="submit"
            disabled={!input.trim() || isProcessing}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AssistantPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading AI Assistant...</div>}>
      <AssistantContent />
    </Suspense>
  );
}
