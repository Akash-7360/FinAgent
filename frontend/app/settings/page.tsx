"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Settings as SettingsIcon, Sliders, Shield, Bell, CheckCircle2, User } from "lucide-react";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75);
  const [anomalySensitivity, setAnomalySensitivity] = useState(0.7);
  const [budgetAlertThreshold, setBudgetAlertThreshold] = useState(0.8);
  const [enableProactive, setEnableProactive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (user?.preferences) {
      setConfidenceThreshold(user.preferences.confidence_threshold);
      setAnomalySensitivity(user.preferences.anomaly_sensitivity);
      setBudgetAlertThreshold(user.preferences.budget_alert_threshold);
      setEnableProactive(user.preferences.enable_proactive_alerts);
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);
    try {
      await api.updatePreferences({
        confidence_threshold: confidenceThreshold,
        anomaly_sensitivity: anomalySensitivity,
        budget_alert_threshold: budgetAlertThreshold,
        enable_proactive_alerts: enableProactive,
      });
      await refreshUser();
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      alert(`Error updating preferences: ${err}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-indigo-400" />
          <span>Agent Configuration & Settings</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Tune agent reasoning sensitivity, clarification triggers, and autonomous notification thresholds.
        </p>
      </div>

      {/* Supabase & Vercel Cloud Deployment Info Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900/90 to-indigo-950/40 border border-emerald-500/30 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">
              Supabase & Vercel Cloud Deployment
            </h3>
          </div>
          <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
            Production Ready
          </span>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          FinAgent is architected to run with <b>Supabase</b> as the primary PostgreSQL + pgvector database
          and <b>Vercel</b> for the high-performance Next.js frontend deployment.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
            <span className="font-semibold text-emerald-400 block mb-1">1. Supabase Database URL</span>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              In your Supabase project settings, copy the <b>URI</b> (port 5432 or 6543) and set it in your backend environment:
            </p>
            <code className="mt-1.5 block p-2 rounded-lg bg-slate-900 border border-slate-800 text-[10px] text-indigo-300 font-mono select-all">
              DATABASE_URL="postgresql+psycopg2://postgres:[PASS]@db.[REF].supabase.co:5432/postgres"
            </code>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
            <span className="font-semibold text-indigo-400 block mb-1">2. Vercel Frontend Setup</span>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              In Vercel project settings, set your deployed backend API URL (Render/Railway/Modal/Fly.io):
            </p>
            <code className="mt-1.5 block p-2 rounded-lg bg-slate-900 border border-slate-800 text-[10px] text-indigo-300 font-mono select-all">
              NEXT_PUBLIC_API_URL="https://your-finagent-api.onrender.com/api"
            </code>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
          <span className="font-semibold text-amber-400 block mb-1">3. OpenAI API Key</span>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Set your OpenAI API key in your backend <code>.env</code>. If omitted, FinAgent automatically runs with its intelligent built-in rule & statistical reasoning engine!
          </p>
          <code className="mt-1.5 block p-2 rounded-lg bg-slate-900 border border-slate-800 text-[10px] text-amber-300 font-mono select-all">
            OPENAI_API_KEY="sk-proj-..."
          </code>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Details Card */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <User className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Profile & Identity</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.full_name || "Akash U"}
                className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || "demo@finagent.ai"}
                className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Currency Symbol</label>
              <input
                type="text"
                disabled
                value="₹ (INR)"
                className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Monthly Income</label>
              <input
                type="text"
                disabled
                value={`₹${(user?.monthly_income || 125000).toLocaleString()}`}
                className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300"
              />
            </div>
          </div>
        </div>

        {/* Agent Sensitivity Sliders */}
        <div className="glass-panel p-6 rounded-2xl space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Sliders className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">Autonomous Agent Sensitivity</h3>
          </div>

          {/* Slider 1: Confidence Threshold */}
          <div>
            <div className="flex items-center justify-between mb-1.5 text-xs">
              <span className="font-medium text-slate-200">
                Categorization Confidence Threshold
              </span>
              <span className="font-bold text-indigo-400 font-mono">
                {Math.round(confidenceThreshold * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.95"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Transactions below this confidence level (e.g. peer payments like "Paid ₹2,500 to Rahul")
              will halt and ask for user clarification.
            </p>
          </div>

          {/* Slider 2: Anomaly Sensitivity */}
          <div>
            <div className="flex items-center justify-between mb-1.5 text-xs">
              <span className="font-medium text-slate-200">
                3-Layer Anomaly Detection Sensitivity
              </span>
              <span className="font-bold text-amber-400 font-mono">
                {Math.round(anomalySensitivity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.90"
              step="0.05"
              value={anomalySensitivity}
              onChange={(e) => setAnomalySensitivity(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Threshold where combined rule, statistical Z-score, and Isolation Forest ML scores trigger an alert.
            </p>
          </div>

          {/* Slider 3: Budget Warning Limit */}
          <div>
            <div className="flex items-center justify-between mb-1.5 text-xs">
              <span className="font-medium text-slate-200">
                Budget Velocity Alert Threshold
              </span>
              <span className="font-bold text-emerald-400 font-mono">
                {Math.round(budgetAlertThreshold * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.60"
              max="1.00"
              step="0.05"
              value={budgetAlertThreshold}
              onChange={(e) => setBudgetAlertThreshold(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Proactively notifies you when current spending reaches this fraction of your category budget.
            </p>
          </div>
        </div>

        {/* Autonomous Background Monitoring Toggle */}
        <div className="glass-panel p-6 rounded-2xl flex items-center justify-between">
          <div className="space-y-0.5 max-w-md">
            <span className="text-xs font-semibold text-white block">
              Autonomous Proactive Monitoring
            </span>
            <span className="text-[11px] text-slate-400 block">
              Runs periodic scheduled checks for budget overrun projections and duplicate charges.
            </span>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={enableProactive}
              onChange={(e) => setEnableProactive(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
          </label>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-between pt-2">
          {savedSuccess ? (
            <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-4 h-4" /> Preferences updated successfully!
            </span>
          ) : (
            <span></span>
          )}

          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Preferences"}
          </button>
        </div>
      </form>
    </div>
  );
}
