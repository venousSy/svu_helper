import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AppLayout from '../components/layout/AppLayout';
import StatCard from '../components/ui/StatCard';
import { useWithdrawals } from '../hooks/useWithdrawals';
import {
  Banknote, Clock, CheckCircle2, XCircle, Loader2, AlertCircle,
  RefreshCw, ChevronDown, Copy, Check, Send, Ban,
} from 'lucide-react';

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmt(n) {
  return typeof n === 'number' ? n.toLocaleString() : '—';
}
function fmtDate(val) {
  if (!val) return '—';
  try { return new Date(val).toLocaleString('ar-SY', { dateStyle: 'medium', timeStyle: 'short' }); }
  catch { return String(val); }
}
function shortId(id) {
  return id ? `…${String(id).slice(-8)}` : '—';
}

// ── Small components ──────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const map = {
    pending:   { label: 'قيد الانتظار', cls: 'bg-amber-500/15 text-amber-400 border-amber-500/30' },
    processed: { label: 'مدفوع', cls: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
    rejected:  { label: 'مرفوض', cls: 'bg-red-500/15 text-red-400 border-red-500/30' },
  };
  const cfg = map[status] || { label: status, cls: 'bg-surface-elevated text-text-secondary border-border' };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button onClick={handleCopy} className="p-1 rounded hover:bg-surface-elevated transition-colors text-text-muted hover:text-text-primary" title="Copy">
      {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
    </button>
  );
}

// ── Mark Paid inline form ─────────────────────────────────────────────────────

function MarkPaidForm({ requestId, amount, onConfirm, onCancel, isLoading }) {
  const [ref, setRef] = useState('');
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="mt-3 p-3 rounded-lg bg-surface border border-emerald-500/20 space-y-2"
    >
      <p className="text-xs text-text-secondary">
        تأكيد دفع <strong className="text-emerald-400">{fmt(amount)} ل.س</strong>
      </p>
      <input
        type="text"
        value={ref}
        onChange={e => setRef(e.target.value)}
        placeholder="رقم العملية (اختياري)"
        className="w-full bg-surface-elevated border border-border rounded-md px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-emerald-500/50 transition-colors"
      />
      <div className="flex gap-2">
        <button
          onClick={() => onConfirm(ref || null)}
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-semibold rounded-md bg-emerald-500 hover:bg-emerald-400 text-white disabled:opacity-60 transition-colors"
        >
          {isLoading ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
          تأكيد الدفع
        </button>
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 py-1.5 text-xs font-semibold rounded-md border border-border text-text-secondary hover:bg-surface-elevated disabled:opacity-60 transition-colors"
        >
          إلغاء
        </button>
      </div>
    </motion.div>
  );
}

// ── Reject confirm dialog ─────────────────────────────────────────────────────

function RejectConfirm({ amount, onConfirm, onCancel, isLoading }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="mt-3 p-3 rounded-lg bg-surface border border-red-500/20 space-y-2"
    >
      <p className="text-xs text-text-secondary">
        رفض الطلب وإعادة <strong className="text-red-400">{fmt(amount)} ل.س</strong> إلى رصيد المستخدم؟
      </p>
      <div className="flex gap-2">
        <button
          onClick={onConfirm}
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-semibold rounded-md bg-red-500 hover:bg-red-400 text-white disabled:opacity-60 transition-colors"
        >
          {isLoading ? <Loader2 size={12} className="animate-spin" /> : <Ban size={12} />}
          تأكيد الرفض
        </button>
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 py-1.5 text-xs font-semibold rounded-md border border-border text-text-secondary hover:bg-surface-elevated disabled:opacity-60 transition-colors"
        >
          إلغاء
        </button>
      </div>
    </motion.div>
  );
}

// ── Withdrawal card ───────────────────────────────────────────────────────────

function WithdrawalCard({ req, onMarkPaid, onReject }) {
  const [expanded, setExpanded] = useState(false);
  const [showPayForm, setShowPayForm] = useState(false);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);

  const isPending = req.status === 'pending';
  const isProcessed = req.status === 'processed';
  const isRejected = req.status === 'rejected';

  const handleMarkPaid = async (shamcashRef) => {
    setActionLoading(true);
    setActionError(null);
    try {
      await onMarkPaid(req.request_id, shamcashRef);
      setShowPayForm(false);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    setActionError(null);
    try {
      await onReject(req.request_id);
      setShowRejectForm(false);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <motion.div
      layout
      className={`glass rounded-xl border overflow-hidden transition-shadow duration-300 hover:shadow-[0_8px_30px_rgba(0,0,0,0.3)] ${
        isPending
          ? 'border-amber-500/40 shadow-[0_0_0_1px_rgba(245,158,11,0.15)]'
          : isProcessed
          ? 'border-emerald-500/25'
          : 'border-red-500/25'
      }`}
    >
      {/* Pending pulse bar */}
      {isPending && (
        <div className="h-0.5 bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 animate-pulse" />
      )}

      {/* Card header — always visible */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-surface-elevated/40 transition-colors"
      >
        <div className="flex items-center gap-4">
          <div className={`flex items-center justify-center w-10 h-10 rounded-full border font-bold text-sm ${
            isPending ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            : isProcessed ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            {isPending ? <Clock size={18} /> : isProcessed ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <p className="text-sm font-bold text-text-primary">User {req.user_id}</p>
              <StatusBadge status={req.status} />
            </div>
            <p className="text-xs text-text-muted mt-0.5 font-mono">{shortId(req.request_id)}</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-text-muted uppercase tracking-widest font-semibold mb-0.5">المبلغ</p>
            <p className={`text-base font-bold ${isPending ? 'text-amber-400' : isProcessed ? 'text-emerald-400' : 'text-red-400'}`}>
              {fmt(req.amount)} ل.س
            </p>
          </div>
          <div className="text-right hidden lg:block">
            <p className="text-[10px] text-text-muted uppercase tracking-widest font-semibold mb-0.5">الرصيد الحالي</p>
            <p className="text-sm font-semibold text-text-primary">{fmt(req.current_balance)} ل.س</p>
          </div>
          <motion.div animate={{ rotate: expanded ? 180 : 0 }} className="text-text-muted bg-surface-elevated p-1.5 rounded-md border border-border">
            <ChevronDown size={14} />
          </motion.div>
        </div>
      </button>

      {/* Expanded detail panel */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-border/50"
          >
            <div className="px-5 py-4 space-y-4 bg-surface/30">

              {/* Info grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <InfoRow label="الاسم (ShamCash)" value={req.shamcash_name} />
                <InfoRow label="العنوان (ShamCash)" value={req.shamcash_address} copyable />
                <InfoRow label="طلب بتاريخ" value={fmtDate(req.requested_at)} />
                {(isProcessed || isRejected) && (
                  <InfoRow label="مُعالَج بتاريخ" value={fmtDate(req.processed_at)} />
                )}
                {isProcessed && req.shamcash_ref && (
                  <InfoRow label="رقم العملية" value={req.shamcash_ref} copyable />
                )}
                {isRejected && (
                  <InfoRow label="ملاحظة" value="تمت إعادة الرصيد للمستخدم" />
                )}
                <InfoRow label="رقم الطلب الكامل" value={req.request_id} copyable />
              </div>

              {/* Mobile amount */}
              <div className="flex sm:hidden items-center justify-between text-sm text-text-secondary">
                <span>المبلغ: <strong className={`${isPending ? 'text-amber-400' : isProcessed ? 'text-emerald-400' : 'text-red-400'}`}>{fmt(req.amount)} ل.س</strong></span>
                <span>الرصيد: <strong className="text-text-primary">{fmt(req.current_balance)} ل.س</strong></span>
              </div>

              {/* Action buttons (pending only) */}
              {isPending && !showPayForm && !showRejectForm && (
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setShowPayForm(true); setShowRejectForm(false); setActionError(null); }}
                    className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                  >
                    <Send size={13} /> تأكيد الدفع
                  </button>
                  <button
                    onClick={() => { setShowRejectForm(true); setShowPayForm(false); setActionError(null); }}
                    className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-colors"
                  >
                    <Ban size={13} /> رفض الطلب
                  </button>
                </div>
              )}

              {/* Error message */}
              {actionError && (
                <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">
                  ❌ {actionError}
                </p>
              )}

              {/* Inline forms */}
              <AnimatePresence>
                {showPayForm && (
                  <MarkPaidForm
                    requestId={req.request_id}
                    amount={req.amount}
                    onConfirm={handleMarkPaid}
                    onCancel={() => setShowPayForm(false)}
                    isLoading={actionLoading}
                  />
                )}
                {showRejectForm && (
                  <RejectConfirm
                    amount={req.amount}
                    onConfirm={handleReject}
                    onCancel={() => setShowRejectForm(false)}
                    isLoading={actionLoading}
                  />
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function InfoRow({ label, value, copyable = false }) {
  return (
    <div>
      <p className="text-[10px] text-text-muted uppercase tracking-widest font-semibold mb-0.5">{label}</p>
      <div className="flex items-center gap-1">
        <p className="text-sm text-text-primary font-medium break-all">{value || '—'}</p>
        {copyable && value && <CopyButton text={value} />}
      </div>
    </div>
  );
}

// ── Status tabs ───────────────────────────────────────────────────────────────

const TABS = [
  { key: null,        label: 'الكل' },
  { key: 'pending',   label: 'قيد الانتظار' },
  { key: 'processed', label: 'مدفوع' },
  { key: 'rejected',  label: 'مرفوض' },
];

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function Withdrawals() {
  const [activeTab, setActiveTab] = useState(null);
  const { requests, stats, isLoading, error, refetch, markPaid, rejectRequest } =
    useWithdrawals(activeTab);

  const visibleRequests = requests.filter(r => !activeTab || r.status === activeTab);

  return (
    <AppLayout title="Withdrawals">
      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <StatCard
          title="Pending"
          value={fmt(stats.pending_count)}
          subtitle="Awaiting manual transfer"
          icon={Clock}
          color="amber"
        />
        <StatCard
          title="Total Paid"
          value={`${fmt(stats.total_paid_syp)} ل.س`}
          subtitle="Successfully transferred"
          icon={Banknote}
          color="green"
        />
        <StatCard
          title="Rejected"
          value={fmt(stats.rejected_count)}
          subtitle="Balance restored to users"
          icon={XCircle}
          color="red"
        />
      </div>

      {/* Tab bar */}
      <div className="glass rounded-xl border border-border p-6">
        <div className="flex flex-wrap items-center gap-2 mb-6">
          {TABS.map(tab => (
            <button
              key={String(tab.key)}
              onClick={() => setActiveTab(tab.key)}
              className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === tab.key
                  ? 'text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
              }`}
            >
              {activeTab === tab.key && (
                <motion.div
                  layoutId="tab-active"
                  className="absolute inset-0 bg-brand-primary rounded-lg shadow-[0_4px_20px_rgba(59,130,246,0.4)]"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <span className="relative z-10">{tab.label}</span>
              {tab.key === 'pending' && stats.pending_count > 0 && (
                <span className="relative z-10 ml-1.5 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  {stats.pending_count}
                </span>
              )}
            </button>
          ))}

          <button
            onClick={refetch}
            className="ml-auto p-2 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors"
            title="Refresh"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Content */}
        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <AlertCircle className="w-8 h-8 text-brand-danger" />
            <p className="text-text-secondary text-sm">{error}</p>
            <button
              onClick={refetch}
              className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-brand-primary text-white hover:opacity-90 transition-opacity"
            >
              <RefreshCw size={14} /> Retry
            </button>
          </div>
        )}

        {!isLoading && !error && visibleRequests.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 rounded-xl border border-dashed border-border">
            <Banknote className="w-8 h-8 text-text-muted" />
            <p className="text-text-muted text-sm">لا توجد طلبات سحب في هذه الفئة</p>
          </div>
        )}

        {!isLoading && !error && visibleRequests.length > 0 && (
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {visibleRequests.map(req => (
                <WithdrawalCard
                  key={req.request_id}
                  req={req}
                  onMarkPaid={markPaid}
                  onReject={rejectRequest}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
