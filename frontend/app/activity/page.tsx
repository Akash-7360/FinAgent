"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  Activity,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Cpu,
  Layers,
  Filter
} from "lucide-react";

export default function ActivityPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchEvents = async () => {
    try {
      const data = await api.getAgentEvents(60);
      setEvents(data);
    } catch (err) {
      console.error("Error fetching agent events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 12000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-indigo-400" />
            <span>Agent Observability & Audit Trail</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time execution traces of autonomous decisions, tool arguments, and latency audits.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span className="text-xs text-emerald-400 font-semibold">Live Event Stream</span>
        </div>
      </div>

      {/* Observability Visual Flow Card */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between flex-wrap gap-2 text-xs text-slate-400">
        <div className="flex items-center gap-1.5 font-medium text-slate-200">
          <Terminal className="w-4 h-4 text-indigo-400" />
          <span>User Input</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
        <div className="flex items-center gap-1.5 font-medium text-slate-200">
          <Layers className="w-4 h-4 text-amber-400" />
          <span>Confidence Check</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
        <div className="flex items-center gap-1.5 font-medium text-slate-200">
          <Cpu className="w-4 h-4 text-purple-400" />
          <span>Dynamic Tool Calling</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
        <div className="flex items-center gap-1.5 font-medium text-slate-200">
          <Activity className="w-4 h-4 text-blue-400" />
          <span>Observe & Reason</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
        <div className="flex items-center gap-1.5 font-medium text-slate-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Synthesize / Proactive Alert</span>
        </div>
      </div>

      {/* Events Timeline Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-white">Event Log ({events.length})</span>
          <span className="text-[11px] text-slate-500">Auto-refreshing</span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {loading ? (
            <div className="py-16 text-center text-xs text-slate-500">Loading observability records...</div>
          ) : events.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-500">No agent events logged yet.</div>
          ) : (
            events.map((ev) => (
              <div key={ev.id} className="p-4 hover:bg-slate-900/40 transition-colors space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        ev.agent_state.includes("Alert")
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : ev.agent_state.includes("Clarification")
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          : "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      }`}
                    >
                      {ev.agent_state}
                    </span>

                    {ev.tool_called && (
                      <span className="font-mono text-[11px] text-indigo-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {ev.tool_called}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-slate-500 text-[11px]">
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3" /> {ev.execution_time_ms}ms
                    </span>
                    <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Decision */}
                <p className="text-xs text-slate-200 font-medium">{ev.decision}</p>

                {/* Result Summary */}
                {ev.tool_result_summary && (
                  <p className="text-[11px] text-slate-400 font-mono bg-slate-950/60 p-2 rounded-lg border border-slate-800/80 truncate">
                    {ev.tool_result_summary}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
