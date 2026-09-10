"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";

interface Toast {
  id: string;
  type: "success" | "error" | "info" | "warning";
  message: string;
}

interface ToastContextType {
  toast: (message: string, type?: "success" | "error" | "info" | "warning") => void;
}

const ToastContext = createContext<ToastContextType>({
  toast: () => {},
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: "success" | "error" | "info" | "warning" = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto p-3.5 rounded-2xl glass-panel shadow-2xl flex items-center justify-between gap-3 text-xs font-medium border animate-in slide-in-from-bottom-3 duration-200 ${
              t.type === "error"
                ? "border-rose-500/40 bg-rose-950/80 text-rose-200"
                : t.type === "warning"
                ? "border-amber-500/40 bg-amber-950/80 text-amber-200"
                : t.type === "info"
                ? "border-indigo-500/40 bg-indigo-950/80 text-indigo-200"
                : "border-emerald-500/40 bg-slate-900/95 text-emerald-300"
            }`}
          >
            <div className="flex items-center gap-2.5">
              {t.type === "error" || t.type === "warning" ? (
                <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
              ) : t.type === "info" ? (
                <Info className="w-4 h-4 shrink-0 text-indigo-400" />
              ) : (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              )}
              <span className="leading-snug">{t.message}</span>
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="text-slate-400 hover:text-white p-1 rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
