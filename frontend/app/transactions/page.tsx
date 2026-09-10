"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import {
  Search,
  Filter,
  Plus,
  Upload,
  AlertTriangle,
  FileSpreadsheet,
  CheckCircle2,
  Trash2,
  Calendar,
  Layers,
  ArrowUpDown,
  Download,
  Receipt
} from "lucide-react";

const CATEGORIES = [
  "All",
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

export default function TransactionsPage() {
  const { toast } = useToast();
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [anomalyOnly, setAnomalyOnly] = useState(false);

  // Manual Add Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAmount, setNewAmount] = useState("");
  const [newMerchant, setNewMerchant] = useState("");
  const [newCategory, setNewCategory] = useState("Food");
  const [newDate, setNewDate] = useState(new Date().toISOString().split("T")[0]);
  const [newDesc, setNewDesc] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // CSV Import Modal state
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<any>(null);
  const [isImporting, setIsImporting] = useState(false);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      const data = await api.getExpenses({
        category: categoryFilter,
        merchant: search || undefined,
        is_anomaly: anomalyOnly ? true : undefined,
      });
      setExpenses(data);
    } catch (err) {
      console.error("Error fetching transactions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [categoryFilter, anomalyOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchExpenses();
  };

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAmount || !newMerchant) return;
    setIsSubmitting(true);
    try {
      const res = await api.createExpense({
        amount: parseFloat(newAmount),
        merchant: newMerchant,
        category: newCategory,
        date: newDate,
        description: newDesc,
      });
      setShowAddModal(false);
      setNewAmount("");
      setNewMerchant("");
      setNewDesc("");
      await fetchExpenses();
      if (res.is_anomaly) {
        toast(`⚠️ Anomaly detected! ${res.anomaly_reason || ""}`, "warning");
      } else {
        toast("Expense successfully logged and verified!", "success");
      }
    } catch (err: any) {
      toast(`Failed to add expense: ${err.message}`, "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this transaction?")) return;
    try {
      await api.deleteExpense(id);
      setExpenses((prev) => prev.filter((e) => e.id !== id));
      toast("Transaction deleted from ledger", "info");
    } catch (err: any) {
      toast(`Error deleting: ${err.message}`, "error");
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setIsImporting(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    try {
      const res = await api.importCSV(formData);
      setImportResult(res);
      await fetchExpenses();
      toast(`Imported ${res.imported_count} transactions (${res.anomalies_detected} anomalies detected)!`, "success");
    } catch (err: any) {
      toast(`Import error: ${err.message}`, "error");
    } finally {
      setIsImporting(false);
    }
  };

  const downloadSampleCSV = () => {
    const csvContent =
      "Date,Merchant,Amount,Category,PaymentMethod,Description\n" +
      "2026-09-01,Starbucks,480.00,Food,UPI,Morning latte and croissant\n" +
      "2026-09-02,Uber,380.00,Transport,Card,Cab to office\n" +
      "2026-09-03,Blinkit,1250.00,Groceries,UPI,Weekly milk and veggies\n" +
      "2026-09-04,Zara,3499.00,Shopping,Card,Casual t-shirts\n" +
      "2026-09-05,PVR Cinemas,850.00,Entertainment,Card,Weekend movie tickets\n" +
      "2026-09-06,Airtel Broadband,1179.00,Bills,NetBanking,Monthly fiber internet bill\n" +
      "2026-09-07,Bastian Fine Dining,4500.00,Food,Card,Celebration luxury dinner\n" +
      "2026-09-08,Apollo Pharmacy,420.00,Healthcare,UPI,Cold medicine and vitamins\n" +
      "2026-09-09,Netflix,649.00,Subscriptions,Card,Monthly 4K streaming plan\n" +
      "2026-09-10,Rahul,2500.00,,UPI,Paid 2500 to Rahul\n";

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "sample_expenses.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast("Downloaded sample_expenses.csv", "info");
  };

  const totalAmount = expenses.reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
  const anomalyCount = expenses.filter((e) => e.is_anomaly).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Transactions & Ledger</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manual expense logging, smart CSV imports with fuzzy mapping, and AI anomaly auditing.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          <button
            onClick={downloadSampleCSV}
            title="Download ready-to-test CSV sample"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-slate-700 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Sample CSV</span>
          </button>

          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-medium border border-slate-700 transition-all hover:border-slate-600"
          >
            <Upload className="w-3.5 h-3.5 text-indigo-400" />
            <span>Import CSV</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-500/20 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Expense</span>
          </button>
        </div>
      </div>

      {/* Summary Stat Badges Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">Total Filtered</span>
          <span className="text-sm font-bold text-white">{expenses.length} records</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">Total Sum</span>
          <span className="text-sm font-bold text-emerald-400">₹{totalAmount.toLocaleString()}</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">Anomalies</span>
          <span className={`text-sm font-bold ${anomalyCount > 0 ? "text-rose-400" : "text-slate-400"}`}>
            {anomalyCount} flagged
          </span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by merchant, description..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
          />
        </form>

        <div className="flex items-center flex-wrap gap-2.5">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Anomaly Toggle */}
          <button
            onClick={() => setAnomalyOnly(!anomalyOnly)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              anomalyOnly
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Anomalies Only</span>
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Merchant & Note</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Status / Anomaly</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    Loading transactions...
                  </td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No transactions match current filters.
                  </td>
                </tr>
              ) : (
                expenses.map((exp) => (
                  <tr key={exp.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-200">
                      <div>{exp.merchant}</div>
                      {exp.description && (
                        <div className="text-[11px] text-slate-500 truncate max-w-xs">{exp.description}</div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                        {exp.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{exp.date}</td>
                    <td className="py-3 px-4 text-slate-400">{exp.payment_method || "Card"}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-[11px] font-medium ${
                          exp.confidence_score >= 0.8
                            ? "text-emerald-400"
                            : exp.confidence_score >= 0.6
                            ? "text-amber-400"
                            : "text-rose-400"
                        }`}
                      >
                        {Math.round(exp.confidence_score * 100)}%
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {exp.is_anomaly ? (
                        <span
                          title={exp.anomaly_reason || "Flagged by 3-layer anomaly engine"}
                          className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] font-semibold flex items-center gap-1 w-fit cursor-help"
                        >
                          <AlertTriangle className="w-3 h-3" /> Anomaly ({exp.anomaly_score})
                        </span>
                      ) : (
                        <span className="text-[10px] text-emerald-400/80 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Normal
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-white">
                      ₹{Number(exp.amount).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleDelete(exp.id)}
                        className="text-slate-500 hover:text-rose-400 p-1 rounded"
                        title="Delete expense"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Add Expense Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-panel w-full max-w-md rounded-2xl p-6 shadow-2xl border border-slate-700">
            <h3 className="text-base font-bold text-white mb-4">Log New Expense</h3>
            <form onSubmit={handleCreateExpense} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newAmount}
                  onChange={(e) => setNewAmount(e.target.value)}
                  placeholder="e.g. 4500"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Merchant / Payee</label>
                <input
                  type="text"
                  required
                  value={newMerchant}
                  onChange={(e) => setNewMerchant(e.target.value)}
                  placeholder="e.g. Bastian Restaurant or Rahul"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    {CATEGORIES.filter((c) => c !== "All").map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1">Date</label>
                  <input
                    type="date"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Description (Optional)</label>
                <input
                  type="text"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="e.g. Team celebration dinner"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-500/20 disabled:opacity-50"
                >
                  {isSubmitting ? "Evaluating..." : "Save Expense"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Smart CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-panel w-full max-w-lg rounded-2xl p-6 shadow-2xl border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Smart CSV Transaction Import</h3>
              </div>
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setImportResult(null);
                }}
                className="text-slate-400 hover:text-white text-xs"
              >
                Close
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Our intelligent mapping layer auto-detects columns such as <code>amount/price</code>,{" "}
              <code>merchant/payee</code>, <code>date</code>, and <code>category</code>. Every row is routed through
              the agent categorizer and 3-layer anomaly detection engine.
            </p>

            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-2xl p-6 text-center cursor-pointer transition-colors bg-slate-900/50">
                <input
                  type="file"
                  accept=".csv,.txt"
                  id="csvFile"
                  className="hidden"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                />
                <label htmlFor="csvFile" className="cursor-pointer block">
                  <Upload className="w-8 h-8 text-indigo-400 mx-auto mb-2 opacity-80" />
                  <span className="text-xs text-slate-200 font-medium block">
                    {selectedFile ? selectedFile.name : "Click to select CSV file"}
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-1">Supports UTF-8 CSV exports from any bank</span>
                </label>
              </div>

              {importResult && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs">
                  <div className="font-semibold text-emerald-400 mb-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Import Completed!
                  </div>
                  <div className="text-slate-300">
                    Imported: <b>{importResult.imported_count}</b> transactions.
                  </div>
                  <div className="text-amber-300 mt-0.5">
                    Anomalies flagged: <b>{importResult.anomalies_detected}</b>.
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowImportModal(false);
                    setImportResult(null);
                  }}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
                >
                  Done
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || isImporting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-500/20 disabled:opacity-50"
                >
                  {isImporting ? "Processing Pipeline..." : "Upload & Process"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
