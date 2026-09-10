"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Layers,
  Activity,
  Repeat,
  Calendar,
  Sparkles
} from "lucide-react";

export default function InsightsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [alertList, expList] = await Promise.all([
        api.getAlerts(),
        api.getExpenses({ is_anomaly: true }),
      ]);
      setAlerts(alertList);
      setAnomalies(expList);
    } catch (err) {
      console.error("Error loading insights:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleResolveAlert = async (id: string) => {
    try {
      await api.resolveAlert(id);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, is_resolved: true } : a))
      );
    } catch (err) {
      alert(`Error resolving: ${err}`);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <Sparkles className="w-6 h-6 text-indigo-400" />
          <span>Insights & 3-Layer Anomaly Detection</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Deep-dive analysis of Rule constraints, Statistical Z-score deviations, and Isolation Forest ML models.
        </p>
      </div>

      {/* 3-Layer Architectural Infographic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Layer 1 */}
        <div className="glass-panel p-5 rounded-2xl border-t-2 border-t-amber-400">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider">
              Layer 1
            </span>
            <div className="p-1.5 rounded-lg bg-amber-500/15 text-amber-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <h3 className="text-sm font-bold text-white">Rule-Based Constraints</h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Evaluates hard boundaries such as single expenses exceeding 3.0x category averages,
            first-time luxury dining spikes, and duplicate-looking transaction pairs.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-300 font-mono">
            amount &gt; 3.0 × cat_avg
          </div>
        </div>

        {/* Layer 2 */}
        <div className="glass-panel p-5 rounded-2xl border-t-2 border-t-blue-400">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] uppercase font-bold text-blue-400 tracking-wider">
              Layer 2
            </span>
            <div className="p-1.5 rounded-lg bg-blue-500/15 text-blue-400">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <h3 className="text-sm font-bold text-white">Statistical Distribution</h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Computes standard Z-score standard deviations (Z &gt; 2.2σ) and Interquartile Range
            (IQR upper fence = Q3 + 1.5×IQR) across rolling 90-day spending history.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-300 font-mono">
            Z = (x - μ) / σ &gt; 2.2
          </div>
        </div>

        {/* Layer 3 */}
        <div className="glass-panel p-5 rounded-2xl border-t-2 border-t-purple-400">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] uppercase font-bold text-purple-400 tracking-wider">
              Layer 3
            </span>
            <div className="p-1.5 rounded-lg bg-purple-500/15 text-purple-400">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <h3 className="text-sm font-bold text-white">Isolation Forest (ML)</h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Scikit-learn unsupervised tree ensemble trained on multidimensional features: amount,
            category encoding, day of week, hour, and merchant frequency.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-300 font-mono">
            IsolationForest(c=0.08)
          </div>
        </div>
      </div>

      {/* Flagged Anomaly Incidents */}
      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white">Flagged Spending Anomalies</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Transactions exceeding composite anomaly sensitivity threshold
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/30 font-semibold">
            {anomalies.length} Flagged
          </span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {anomalies.length === 0 ? (
            <div className="py-10 text-center text-xs text-slate-500">
              No anomalies recorded! All transactions conform to baseline behavior.
            </div>
          ) : (
            anomalies.map((a) => (
              <div key={a.id} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-100">{a.merchant}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {a.category}
                    </span>
                    <span className="text-xs text-slate-500">• {a.date}</span>
                  </div>
                  <p className="text-xs text-rose-300 leading-snug">
                    {a.anomaly_reason || "Multi-layer anomaly detected by agentic ensemble"}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block">Anomaly Risk</span>
                    <span className="text-xs font-bold text-rose-400">
                      Score: {a.anomaly_score}
                    </span>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block">Amount</span>
                    <span className="text-sm font-bold text-white">
                      ₹{Number(a.amount).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Autonomous Notifications & Alert Log */}
      <div className="glass-panel p-6 rounded-2xl">
        <h3 className="text-sm font-bold text-white mb-1">Autonomous Alert History</h3>
        <p className="text-xs text-slate-400 mb-4">
          All proactive notifications generated by background monitors and anomaly pipelines
        </p>

        <div className="divide-y divide-slate-800/60">
          {alerts.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">No alert events recorded.</div>
          ) : (
            alerts.map((al) => (
              <div key={al.id} className="py-3 flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <AlertTriangle
                    className={`w-4 h-4 shrink-0 mt-0.5 ${
                      al.severity === "high" ? "text-rose-400" : "text-amber-400"
                    }`}
                  />
                  <div>
                    <span className="text-xs font-semibold text-slate-200 block">{al.title}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5 max-w-2xl leading-relaxed">
                      {al.message}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {al.is_resolved ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Resolved
                    </span>
                  ) : (
                    <button
                      onClick={() => handleResolveAlert(al.id)}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
