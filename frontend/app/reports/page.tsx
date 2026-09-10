"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  FileBarChart,
  Printer,
  Calendar,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Receipt,
  Download,
  CheckCircle2
} from "lucide-react";

export default function ReportsPage() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());

  const generateReport = async (m = month, y = year) => {
    setLoading(true);
    try {
      const data = await api.generateMonthlyReport(m, y);
      setReport(data);
    } catch (err) {
      console.error("Error generating report:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    generateReport();
  }, []);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Controls (Hidden during print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileBarChart className="w-6 h-6 text-indigo-400" />
            <span>Monthly Financial Intelligence Report</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated spending audit, anomaly summaries, budget adherence, and AI guidance.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={month}
            onChange={(e) => {
              const m = parseInt(e.target.value);
              setMonth(m);
              generateReport(m, year);
            }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) => (
              <option key={m} value={m}>
                {new Date(2026, m - 1).toLocaleString("default", { month: "long" })}
              </option>
            ))}
          </select>

          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Export as PDF</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-24 text-center text-xs text-slate-500">Compiling financial intelligence report...</div>
      ) : !report ? (
        <div className="py-24 text-center text-xs text-slate-500">No report data generated.</div>
      ) : (
        /* Printable Report Document */
        <div className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-8 bg-slate-950/90 print:bg-white print:text-black print:p-0 print:border-none print:shadow-none">
          {/* Document Header */}
          <div className="flex items-center justify-between pb-6 border-b border-slate-800 print:border-slate-300">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight text-white print:text-black">
                  FinAgent Intelligence Report
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 print:border-slate-400 print:text-slate-800 font-semibold">
                  Official Statement
                </span>
              </div>
              <p className="text-xs text-slate-400 print:text-slate-600 mt-1">
                Period: <b>{report.month_name}</b> • Generated for Akash U
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-400 print:text-slate-600 block">Total Expenditure</span>
              <span className="text-2xl font-extrabold text-white print:text-black">
                ₹{Number(report.total_spent).toLocaleString()}
              </span>
            </div>
          </div>

          {/* AI Executive Summary */}
          <div className="p-5 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 print:bg-slate-100 print:border-slate-300">
            <div className="flex items-center gap-2 text-indigo-300 print:text-indigo-800 font-semibold text-xs mb-1.5">
              <Sparkles className="w-4 h-4" />
              <span>AI Executive Summary</span>
            </div>
            <p className="text-xs text-slate-300 print:text-slate-800 leading-relaxed">
              {report.ai_summary}
            </p>
          </div>

          {/* Top Categories & Anomalies */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Category Breakdown */}
            <div>
              <h3 className="text-xs font-bold text-slate-300 print:text-slate-900 uppercase tracking-wider mb-3">
                Category Spending Breakdown
              </h3>
              <div className="space-y-2">
                {Object.entries(report.category_breakdown || {}).map(([cat, amt]: any) => (
                  <div key={cat} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 print:border-slate-200">
                    <span className="text-slate-300 print:text-slate-700">{cat}</span>
                    <span className="font-semibold text-white print:text-black">
                      ₹{Number(amt).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Budget Performance */}
            <div>
              <h3 className="text-xs font-bold text-slate-300 print:text-slate-900 uppercase tracking-wider mb-3">
                Budget Adherence Status
              </h3>
              <div className="space-y-2">
                {Object.entries(report.budget_adherence || {}).map(([cat, b]: any) => {
                  const isExceeded = b.status === "Exceeded";
                  return (
                    <div key={cat} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 print:border-slate-200">
                      <div>
                        <span className="text-slate-300 print:text-slate-700 block">{cat}</span>
                        <span className="text-[10px] text-slate-500">Limit: ₹{b.limit?.toLocaleString()}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-semibold text-white print:text-black block">
                          ₹{b.spent?.toLocaleString()}
                        </span>
                        <span className={`text-[10px] font-semibold ${isExceeded ? "text-rose-400" : "text-emerald-400"}`}>
                          {b.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Top Expenses Recorded */}
          <div>
            <h3 className="text-xs font-bold text-slate-300 print:text-slate-900 uppercase tracking-wider mb-3">
              Largest Individual Transactions
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 print:border-slate-300 text-slate-500 print:text-slate-600">
                  <tr>
                    <th className="py-2">Merchant</th>
                    <th className="py-2">Category</th>
                    <th className="py-2">Date</th>
                    <th className="py-2 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 print:divide-slate-200">
                  {report.top_expenses?.map((e: any) => (
                    <tr key={e.id}>
                      <td className="py-2 font-medium text-slate-200 print:text-slate-900">{e.merchant}</td>
                      <td className="py-2 text-slate-400 print:text-slate-600">{e.category}</td>
                      <td className="py-2 text-slate-400 print:text-slate-600">{e.date}</td>
                      <td className="py-2 text-right font-bold text-white print:text-black">
                        ₹{Number(e.amount).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="text-xs font-bold text-slate-300 print:text-slate-900 uppercase tracking-wider mb-3">
              Autonomous Agent Recommendations
            </h3>
            <ul className="space-y-1.5 list-disc list-inside text-xs text-slate-300 print:text-slate-800">
              {report.recommendations?.map((r: string, idx: number) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
