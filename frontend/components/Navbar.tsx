"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { Bell, Search, RefreshCw, CheckCircle2, AlertTriangle, Menu } from "lucide-react";
import Link from "next/link";

export function Navbar() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [showAlerts, setShowAlerts] = useState(false);
  const [scanning, setScanning] = useState(false);

  const loadAlerts = async () => {
    try {
      const data = await api.getAlerts(false);
      setAlerts(data);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerScan = async () => {
    setScanning(true);
    toast("Initiating autonomous proactive scan...", "info");
    try {
      const res = await api.triggerProactiveScan();
      await loadAlerts();
      toast(res.message || "Autonomous scan complete!", "success");
    } catch (err: any) {
      toast(`Scan error: ${err.message}`, "error");
    } finally {
      setTimeout(() => setScanning(false), 800);
    }
  };

  const handleResolveAlert = async (id: string) => {
    try {
      await api.resolveAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      toast("Alert marked as resolved", "success");
    } catch {
      toast("Failed to resolve alert", "error");
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/60 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Search / Context Indicator */}
      <div className="flex items-center gap-3 w-96">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search transactions, budgets, or ask FinAgent..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 transition-all"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                window.location.href = `/assistant?q=${encodeURIComponent((e.target as HTMLInputElement).value)}`;
              }
            }}
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3.5">
        {/* Proactive Trigger Button */}
        <button
          onClick={handleTriggerScan}
          title="Run Autonomous Proactive Anomaly Scan"
          disabled={scanning}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300 transition-all hover:border-slate-600 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${scanning ? "animate-spin" : ""}`} />
          <span>{scanning ? "Scanning..." : "Autonomous Scan"}</span>
        </button>

        {/* Notifications / Alerts Popover */}
        <div className="relative">
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all"
          >
            <Bell className="w-4 h-4" />
            {alerts.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-[10px] font-bold flex items-center justify-center text-white ring-2 ring-slate-950 animate-pulse">
                {alerts.length}
              </span>
            )}
          </button>

          {showAlerts && (
            <div className="absolute right-0 mt-2 w-88 glass-panel rounded-2xl p-4 shadow-2xl z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="font-semibold text-xs text-slate-200">
                  Agent Notifications ({alerts.length})
                </span>
                <Link
                  href="/insights"
                  onClick={() => setShowAlerts(false)}
                  className="text-[11px] text-indigo-400 hover:underline"
                >
                  View All
                </Link>
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60 mt-2">
                {alerts.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-500">
                    No active anomaly or budget alerts!
                  </div>
                ) : (
                  alerts.slice(0, 5).map((a) => (
                    <div key={a.id} className="py-2.5 flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-medium text-slate-200">{a.title}</p>
                          <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{a.message}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleResolveAlert(a.id)}
                        title="Dismiss"
                        className="text-slate-500 hover:text-emerald-400 p-1 rounded"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Badge */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow">
            {user?.full_name ? user.full_name.charAt(0) : "A"}
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-200">{user?.full_name || "Akash U"}</div>
            <div className="text-[10px] text-slate-400">{user?.email || "demo@finagent.ai"}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
