"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Sparkles,
  Wallet,
  Calendar,
  ArrowUpRight,
  ShieldAlert,
  CreditCard,
  Plus,
  Receipt,
  Bot
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";

const CATEGORY_COLORS: Record<string, string> = {
  Food: "#f97316",
  Groceries: "#10b981",
  Transport: "#3b82f6",
  Shopping: "#ec4899",
  Entertainment: "#8b5cf6",
  Subscriptions: "#06b6d4",
  Bills: "#eab308",
  Healthcare: "#14b8a6",
  Rent: "#ef4444",
  Utilities: "#64748b",
  Transfers: "#a855f7",
  Other: "#6b7280"
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);
  const [monthlyTrends, setMonthlyTrends] = useState<any[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [recentExpenses, setRecentExpenses] = useState<any[]>([]);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [sumRes, trendRes, catRes, expRes, bgtRes, alertRes] = await Promise.all([
        api.getSummary(),
        api.getMonthlyAnalytics(6),
        api.getCategoryAnalytics(),
        api.getExpenses({ limit: 6 }),
        api.getBudgets(),
        api.getAlerts(false),
      ]);

      setSummary(sumRes);
      setMonthlyTrends(trendRes);
      setCategoryData(catRes);
      setRecentExpenses(expRes);
      setBudgets(bgtRes);
      setAlerts(alertRes);
    } catch (err) {
      console.error("Error loading dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-medium tracking-wide">Orchestrating financial intelligence...</span>
        </div>
      </div>
    );
  }

  const isSpendUp = summary?.percentage_change >= 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Financial Intelligence Dashboard
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Autonomous expense monitoring, ML anomaly detection, and real-time velocity projections.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/assistant"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-500/25 transition-all hover:scale-[1.02]"
          >
            <Bot className="w-4 h-4" />
            <span>Ask AI Assistant</span>
          </Link>

          <Link
            href="/transactions"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Add Expense</span>
          </Link>
        </div>
      </div>

      {/* AI Insights & Proactive Alert Banners */}
      {alerts.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                  Autonomous Anomaly Alert Detected
                </h4>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold">
                  Action Required
                </span>
              </div>
              <p className="text-xs text-slate-200 mt-1 font-medium">{alerts[0].title}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{alerts[0].message}</p>
            </div>
          </div>

          <Link
            href="/insights"
            className="shrink-0 text-xs text-amber-300 font-medium hover:underline flex items-center gap-1"
          >
            <span>Investigate</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Monthly Spending */}
        <div className="glass-panel p-5 rounded-2xl glass-card-hover">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Monthly Spend</span>
            <div className="p-2 rounded-xl bg-indigo-500/15 text-indigo-400">
              <CreditCard className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              ₹{summary?.current_month_spent?.toLocaleString() || "0"}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs">
            {isSpendUp ? (
              <span className="text-rose-400 flex items-center font-semibold">
                <TrendingUp className="w-3.5 h-3.5 mr-0.5" />+{summary?.percentage_change}%
              </span>
            ) : (
              <span className="text-emerald-400 flex items-center font-semibold">
                <TrendingDown className="w-3.5 h-3.5 mr-0.5" />{summary?.percentage_change}%
              </span>
            )}
            <span className="text-slate-500">vs last month (₹{summary?.previous_month_spent?.toLocaleString()})</span>
          </div>
        </div>

        {/* Card 2: Remaining Budget */}
        <div className="glass-panel p-5 rounded-2xl glass-card-hover">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Remaining Budget</span>
            <div className="p-2 rounded-xl bg-emerald-500/15 text-emerald-400">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              ₹{summary?.remaining_budget?.toLocaleString() || "0"}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
            <span>Limit: ₹{summary?.total_budget_limit?.toLocaleString() || "0"}</span>
            <span className="text-slate-600">•</span>
            <span className="text-emerald-400 font-medium">
              {summary?.total_budget_limit > 0
                ? `${Math.max(0, Math.round((summary.remaining_budget / summary.total_budget_limit) * 100))}% left`
                : "No budgets set"}
            </span>
          </div>
        </div>

        {/* Card 3: Top Merchant */}
        <div className="glass-panel p-5 rounded-2xl glass-card-hover">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Top Merchant</span>
            <div className="p-2 rounded-xl bg-purple-500/15 text-purple-400">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 truncate">
            <span className="text-xl font-bold text-white truncate block">
              {summary?.top_merchant?.name || "None"}
            </span>
          </div>
          <div className="mt-2 flex items-center text-xs text-slate-400">
            <span>Spent: </span>
            <span className="text-slate-200 font-semibold ml-1">
              ₹{summary?.top_merchant?.amount?.toLocaleString() || "0"}
            </span>
          </div>
        </div>

        {/* Card 4: Anomaly Alerts */}
        <div className="glass-panel p-5 rounded-2xl glass-card-hover">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Anomalies</span>
            <div className="p-2 rounded-xl bg-rose-500/15 text-rose-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              {summary?.active_alerts_count || 0}
            </span>
            <span className="text-xs text-slate-400">incidents</span>
          </div>
          <div className="mt-2 flex items-center text-xs">
            {summary?.active_alerts_count > 0 ? (
              <span className="text-rose-400 font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping"></span>
                Review recommended
              </span>
            ) : (
              <span className="text-emerald-400 font-medium">All normal</span>
            )}
          </div>
        </div>
      </div>

      {/* AI Insights Card */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900/80 to-purple-950/50 border border-indigo-500/30 shadow-xl">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white tracking-wide">
            Autonomous AI Expense Insight
          </h3>
        </div>
        <div className="space-y-2">
          {summary?.ai_insights?.map((ins: string, idx: number) => (
            <p key={idx} className="text-xs text-slate-300 leading-relaxed pl-3 border-l-2 border-indigo-500/50">
              {ins}
            </p>
          ))}
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Spending Trend Area Chart */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-white">6-Month Spending Trend</h3>
              <p className="text-xs text-slate-400 mt-0.5">Historical trajectory and monthly aggregate spend</p>
            </div>
            <span className="text-xs text-indigo-400 font-medium bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20">
              Monthly Velocity
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyTrends}>
                <defs>
                  <linearGradient id="spendColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month_name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                  formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, "Spent"]}
                />
                <Area
                  type="monotone"
                  dataKey="total_amount"
                  stroke="#6366f1"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#spendColor)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Donut */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white">Category Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Current month breakdown</p>
          </div>

          <div className="h-52 w-full flex items-center justify-center">
            {categoryData.length === 0 ? (
              <span className="text-xs text-slate-500">No category transactions this month</span>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="total_amount"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={52}
                    outerRadius={78}
                    paddingAngle={4}
                  >
                    {categoryData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CATEGORY_COLORS[entry.category] || "#818cf8"}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "12px",
                      fontSize: "12px",
                    }}
                    formatter={(v: any) => `₹${Number(v).toLocaleString()}`}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Legend */}
          <div className="mt-4 space-y-1.5 max-h-32 overflow-y-auto">
            {categoryData.slice(0, 4).map((c) => (
              <div key={c.category} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[c.category] || "#818cf8" }}
                  ></span>
                  <span className="text-slate-300">{c.category}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">{c.percentage}%</span>
                  <span className="text-white font-medium">₹{c.total_amount.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Budgets & Recent Transactions Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Budget Velocity */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Budget Pacing & Velocity</h3>
              <p className="text-xs text-slate-400 mt-0.5">Real-time limits and projection status</p>
            </div>
            <Link href="/budgets" className="text-xs text-indigo-400 hover:underline">
              Manage Budgets
            </Link>
          </div>

          <div className="space-y-4">
            {budgets.slice(0, 4).map((b) => {
              const pct = Math.min(100, Math.round(b.percentage_used || 0));
              const isExceeded = b.is_exceeded;
              const isWarning = b.velocity_status === "warning";

              return (
                <div key={b.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-medium text-slate-200">{b.category}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">
                        ₹{b.spent_so_far?.toLocaleString()} / ₹{b.monthly_limit?.toLocaleString()}
                      </span>
                      <span
                        className={`font-semibold px-2 py-0.5 rounded-full text-[10px] ${
                          isExceeded
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : isWarning
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        }`}
                      >
                        {b.percentage_used}%
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isExceeded ? "bg-rose-500" : isWarning ? "bg-amber-500" : "bg-indigo-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Transactions with Anomaly Badges */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Recent Transactions</h3>
              <p className="text-xs text-slate-400 mt-0.5">Real-time ledger with AI anomaly flags</p>
            </div>
            <Link href="/transactions" className="text-xs text-indigo-400 hover:underline">
              View All
            </Link>
          </div>

          <div className="divide-y divide-slate-800/60">
            {recentExpenses.map((exp) => (
              <div key={exp.id} className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold"
                    style={{
                      backgroundColor: `${CATEGORY_COLORS[exp.category] || "#6366f1"}20`,
                      color: CATEGORY_COLORS[exp.category] || "#818cf8",
                    }}
                  >
                    {exp.category.charAt(0)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-200">{exp.merchant}</span>
                      {exp.is_anomaly && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold flex items-center gap-0.5">
                          <AlertTriangle className="w-2.5 h-2.5" /> Anomaly
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-500">{exp.category} • {exp.date}</span>
                  </div>
                </div>

                <span className="text-xs font-bold text-white">
                  ₹{Number(exp.amount).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
