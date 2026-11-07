import React, { useEffect } from 'react';
import { CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  message: string;
  type?: 'success' | 'info' | 'warning';
}

interface WorkspaceToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const WorkspaceToast: React.FC<WorkspaceToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{
  toast: ToastMessage;
  onDismiss: (id: string) => void;
}> = ({ toast, onDismiss }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 3200);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const bg =
    toast.type === 'success'
      ? 'bg-emerald-900/90 border-emerald-500/50 text-white'
      : toast.type === 'warning'
      ? 'bg-amber-900/90 border-amber-500/50 text-white'
      : 'bg-slate-900/90 border-slate-700/80 text-white';

  const icon =
    toast.type === 'success' ? (
      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
    ) : toast.type === 'warning' ? (
      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
    ) : (
      <Info className="w-4 h-4 text-blue-400 shrink-0" />
    );

  return (
    <div
      className={`pointer-events-auto flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg border shadow-xl backdrop-blur-md text-xs font-medium animate-slide-up transition-all ${bg}`}
    >
      {icon}
      <span className="flex-1">{toast.message}</span>
      <button
        onClick={() => onDismiss(toast.id)}
        className="text-slate-400 hover:text-white p-0.5 rounded transition"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
