"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import {
  PiggyBank,
  Plus,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Clock,
  Edit2,
  Trash2,
  Sparkles,
  Zap
} from "lucide-react";

const CATEGORIES = [
  "Food",
  "Groceries",
  "Transport",
  "Shopping",
  "Entertainment",
  "Bills",
  "Healthcare",
  "Education",
  "Travel",
  "Subscriptions",
  "Rent",
  "Utilities",
  "Transfers",
  "Other",
];

export default function BudgetsPage() {
  const { toast } = useToast();
  const [budgets, setBudgets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [category, setCategory] = useState("Food");
  const [monthlyLimit, setMonthlyLimit] = useState("");
  const [alertThreshold, setAlertThreshold] = useState("0.80");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchBudgets = async () => {
    try {
      const data = await api.getBudgets();
      setBudgets(data);
    } catch (err) {
      console.error("Error fetching budgets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBudgets();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!monthlyLimit) return;
    setIsSubmitting(true);
    try {
      if (editId) {
        await api.updateBudget(editId, {
          monthly_limit: parseFloat(monthlyLimit),
          alert_threshold: parseFloat(alertThreshold),
        });
        toast("Budget updated successfully!", "success");
      } else {
        await api.createBudget({
          category,
          monthly_limit: parseFloat(monthlyLimit),
          alert_threshold: parseFloat(alertThreshold),
        });
        toast(`Budget of ₹${parseFloat(monthlyLimit).toLocaleString()} created for ${category}!`, "success");
      }
      setShowModal(false);
      setEditId(null);
      setMonthlyLimit("");
      await fetchBudgets();
    } catch (err: any) {
      toast(`Error saving budget: ${err.message}`, "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickBuffer = async (b: any, addAmt: number) => {
    try {
      const newLim = parseFloat(b.monthly_limit) + addAmt;
      await api.updateBudget(b.id, { monthly_limit: newLim });
      toast(`Added +₹${addAmt.toLocaleString()} buffer to ${b.category} budget!`, "success");
      await fetchBudgets();
    } catch (err: any) {
      toast(`Failed to add buffer: ${err.message}`, "error");
    }
  };

  const handleEdit = (b: any) => {
    setEditId(b.id);
    setCategory(b.category);
    setMonthlyLimit(String(b.monthly_limit));
    setAlertThreshold(String(b.alert_threshold || 0.8));
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this budget?")) return;
    try {
      await api.deleteBudget(id);
      setBudgets((prev) => prev.filter((b) => b.id !== id));
      toast("Budget removed", "info");
    } catch (err: any) {
      toast(`Error deleting budget: ${err.message}`, "error");
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Category Budgets & Velocity</h1>
          <p className="text-xs text-slate-400 mt-1">
            Dynamic month-end overrun projections, spending velocity analysis, and automated guardrails.
          </p>
        </div>

        <button
          onClick={() => {
            setEditId(null);
            setMonthlyLimit("");
            setShowModal(true);
          }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/25 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Define Budget</span>
        </button>
      </div>

      {/* Budget Grid */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500">Loading budgets and velocity...</div>
      ) : budgets.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl text-center">
          <PiggyBank className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">No Budgets Defined Yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Create monthly category budgets to let FinAgent monitor your spending pace and notify you proactively.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {budgets.map((b) => {
            const isExceeded = b.is_exceeded;
            const isWarning = b.velocity_status === "warning";
            const pct = Math.min(100, Math.round(b.percentage_used || 0));

            return (
              <div
                key={b.id}
                className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between glass-card-hover"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-white">{b.category}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleEdit(b)}
                        className="p-1 rounded text-slate-500 hover:text-slate-200"
                        title="Edit Budget"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(b.id)}
                        className="p-1 rounded text-slate-500 hover:text-rose-400"
                        title="Delete Budget"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Amounts */}
                  <div className="flex items-baseline justify-between mb-2">
                    <div>
                      <span className="text-xs text-slate-500 block">Spent so far</span>
                      <span className="text-lg font-extrabold text-white">
                        ₹{b.spent_so_far?.toLocaleString()}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-500 block">Monthly Limit</span>
                      <span className="text-sm font-semibold text-slate-300">
                        ₹{b.monthly_limit?.toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mb-3">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isExceeded
                          ? "bg-rose-500 shadow-sm shadow-rose-500/50"
                          : isWarning
                          ? "bg-amber-500 shadow-sm shadow-amber-500/50"
                          : "bg-indigo-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>

                  {/* Status Badges & Velocity Details */}
                  <div className="flex items-center justify-between text-xs mb-3">
                    <span className="text-slate-400 font-medium">{b.percentage_used}% used</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center gap-1 ${
                        isExceeded
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          : isWarning
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      }`}
                    >
                      {isExceeded ? (
                        <>
                          <AlertTriangle className="w-2.5 h-2.5" /> Exceeded
                        </>
                      ) : isWarning ? (
                        <>
                          <TrendingUp className="w-2.5 h-2.5" /> Overrun Risk
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-2.5 h-2.5" /> On Track
                        </>
                      )}
                    </span>
                  </div>

                  {/* AI Velocity Recommendation */}
                  <div className="pt-3 border-t border-slate-800/80 mt-2.5">
                    <div className="flex items-start gap-1.5 text-[11px] text-slate-400 leading-relaxed">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                      <span>
                        Projected month-end:{" "}
                        <b className={isWarning || isExceeded ? "text-amber-300" : "text-slate-200"}>
                          ₹{b.projected_spend?.toLocaleString()}
                        </b>
                        {isWarning && " — Velocity indicates likely budget overrun."}
                        {isExceeded && ` — Over by ₹${Math.abs(b.remaining_amount).toLocaleString()}.`}
                      </span>
                    </div>

                    <div className="mt-2.5 flex items-center justify-between text-[10px]">
                      <span className="text-slate-500 font-mono">
                        Daily allowance: ~₹{Math.max(0, Math.round(b.remaining_amount / Math.max(1, 30 - new Date().getDate())))}/day
                      </span>
                      <button
                        onClick={() => handleQuickBuffer(b, 1000)}
                        className="px-2 py-0.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/30 text-indigo-300 font-semibold border border-indigo-500/30 transition-all"
                      >
                        +₹1,000 Buffer
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create / Edit Budget Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-panel w-full max-w-sm rounded-2xl p-6 shadow-2xl border border-slate-700">
            <h3 className="text-base font-bold text-white mb-4">
              {editId ? "Update Budget" : "Create Category Budget"}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Category</label>
                <select
                  disabled={!!editId}
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Monthly Limit (₹)</label>
                <input
                  type="number"
                  step="100"
                  required
                  value={monthlyLimit}
                  onChange={(e) => setMonthlyLimit(e.target.value)}
                  placeholder="e.g. 8000"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Alert Trigger Threshold</label>
                <select
                  value={alertThreshold}
                  onChange={(e) => setAlertThreshold(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="0.70">70% of limit</option>
                  <option value="0.80">80% of limit (Default)</option>
                  <option value="0.90">90% of limit</option>
                  <option value="1.00">100% (Strict limit)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-500/20 disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : editId ? "Save Changes" : "Create Budget"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
