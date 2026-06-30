import { useState } from 'react';
import AppLayout from '../components/layout/AppLayout';
import StatCard from '../components/ui/StatCard';
import { useReferrals } from '../hooks/useReferrals';
import { colors } from '../styles/tokens';
import {
  Users, UserPlus, Banknote, ChevronDown, ChevronRight,
  Loader2, AlertCircle, RefreshCw, GitBranch, Coins,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// ── Helpers ─────────────────────────────────────────────────────────────────

function fmt(n) {
  return typeof n === 'number' ? n.toLocaleString() : '—';
}

function fmtDate(val) {
  if (!val) return '—';
  try {
    return new Date(val).toLocaleDateString('ar-SY', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
  } catch {
    return String(val);
  }
}

// ── Sub-components ───────────────────────────────────────────────────────────

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
    </div>
  );
}

function ErrorMessage({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <AlertCircle className="w-10 h-10 text-brand-danger" />
      <p className="text-text-secondary">{message}</p>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-brand-primary text-text-primary hover:opacity-90 transition-opacity"
      >
        <RefreshCw size={14} /> Retry
      </button>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-48 gap-3 rounded-xl border border-dashed border-border">
      <GitBranch className="w-8 h-8 text-text-muted" />
      <p className="text-text-muted text-sm">No referral activity yet</p>
    </div>
  );
}

/** Badge showing commission amount */
function CommissionBadge({ amount }) {
  if (!amount) return null;
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">
      <Coins size={10} />
      +{fmt(amount)} ل.س
    </span>
  );
}

/** One row per referred user, collapsible to show commission history */
function ReferralRow({ referral }) {
  const [open, setOpen] = useState(false);
  const hasCommissions = referral.commissions?.length > 0;

  return (
    <div className="border border-border/50 rounded-lg overflow-hidden bg-surface-elevated/30">
      <button
        onClick={() => hasCommissions && setOpen(o => !o)}
        className={`w-full flex items-center justify-between px-4 py-3 text-sm transition-colors ${
          hasCommissions
            ? 'hover:bg-surface-elevated cursor-pointer'
            : 'cursor-default opacity-80'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-primary/10 text-brand-primary font-bold text-xs border border-brand-primary/20 shadow-[0_0_10px_rgba(139,92,246,0.1)]">
            {String(referral.user_id).slice(-2)}
          </div>
          <div className="text-left">
            <span className="text-text-primary font-medium">User&nbsp;{referral.user_id}</span>
            <p className="text-[11px] text-text-muted mt-0.5">Joined {fmtDate(referral.joined_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {hasCommissions ? (
            <CommissionBadge
              amount={referral.commissions.reduce((s, c) => s + (c.amount || 0), 0)}
            />
          ) : (
            <span className="text-[11px] text-text-muted">No projects yet</span>
          )}
          {hasCommissions && (
            <motion.div animate={{ rotate: open ? 180 : 0 }} className="text-text-muted">
              <ChevronDown size={14} />
            </motion.div>
          )}
        </div>
      </button>

      {/* Commission log rows */}
      <AnimatePresence>
        {open && hasCommissions && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border/50 divide-y divide-border/30 bg-surface/50 overflow-hidden"
          >
            {referral.commissions.map((c, i) => (
              <div key={i} className="flex items-center justify-between px-6 py-3 text-xs text-text-secondary hover:bg-brand-primary/5 transition-colors">
                <div className="flex items-center gap-2">
                  <span className="text-brand-accent/70 font-mono">#{c.project_id}</span>
                  <span className="text-text-primary font-medium">{c.project_subject || '(no subject)'}</span>
                </div>
                <div className="flex items-center gap-4">
                  <CommissionBadge amount={c.amount} />
                  <span className="text-text-muted">{fmtDate(c.earned_at)}</span>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Card showing one referrer and all their referrals */
function ReferrerCard({ referrer }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="glass rounded-xl border border-border overflow-hidden transition-shadow duration-normal hover:shadow-[0_8px_30px_rgba(0,0,0,0.3)]">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-5 hover:bg-surface-elevated/50 transition-colors relative overflow-hidden"
      >
        <div className="flex items-center gap-4 relative z-10">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-brand-primary/10 border border-brand-primary/30 text-brand-primary font-bold text-sm shadow-[0_0_20px_rgba(139,92,246,0.15)]">
            {String(referrer.referrer_id).slice(-2)}
          </div>
          <div className="text-left">
            <p className="text-base font-bold text-text-primary">User {referrer.referrer_id}</p>
            <p className="text-xs text-brand-accent/80 font-medium mt-0.5">
              {referrer.referral_count} {referrer.referral_count === 1 ? 'referral' : 'referrals'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-8 relative z-10">
          {/* Balance */}
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-text-muted uppercase tracking-widest font-semibold mb-0.5">Balance</p>
            <p className="text-sm font-bold text-text-primary">{fmt(referrer.current_balance)} ل.س</p>
          </div>
          {/* Total earned */}
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-text-muted uppercase tracking-widest font-semibold mb-0.5">Total Earned</p>
            <p className="text-sm font-bold text-brand-success drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]">{fmt(referrer.total_earned)} ل.س</p>
          </div>
          {/* Expand icon */}
          <motion.div animate={{ rotate: expanded ? 180 : 0 }} className="text-text-muted bg-surface-elevated p-1.5 rounded-md border border-border">
            <ChevronDown size={16} />
          </motion.div>
        </div>
      </button>

      {/* Mobile balance strip */}
      <div className="flex sm:hidden items-center justify-between px-5 py-3 bg-surface border-t border-border/50 text-xs text-text-secondary">
        <span>Balance: <strong className="text-text-primary">{fmt(referrer.current_balance)} ل.س</strong></span>
        <span>Earned: <strong className="text-brand-success">{fmt(referrer.total_earned)} ل.س</strong></span>
      </div>

      {/* Referral list */}
      <AnimatePresence>
        {expanded && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-5 py-5 border-t border-border/50 space-y-3 bg-surface/30 overflow-hidden"
          >
            {referrer.referrals.length === 0 ? (
              <p className="text-sm text-text-muted text-center py-6 font-medium">No referrals listed</p>
            ) : (
              referrer.referrals.map((r, i) => (
                <motion.div 
                  key={r.user_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <ReferralRow referral={r} />
                </motion.div>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Referrals() {
  const { summary, tree, isLoading, error, refetch } = useReferrals();
  const [search, setSearch] = useState('');

  const filtered = tree.filter(r =>
    !search || String(r.referrer_id).includes(search)
  );

  return (
    <AppLayout title="Referrals">
      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} onRetry={refetch} />}

      {!isLoading && !error && (
        <div className="space-y-8">

          {/* ── Summary Cards ── */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <StatCard
              title="Referred Users"
              value={fmt(summary?.total_referred_users ?? 0)}
              subtitle="Total users who joined via a link"
              icon={UserPlus}
              color="blue"
            />
            <StatCard
              title="Active Referrers"
              value={fmt(summary?.unique_referrers ?? 0)}
              subtitle="Users whose link was used"
              icon={Users}
              color="purple"
            />
            <StatCard
              title="Commissions Paid"
              value={`${fmt(summary?.total_commissions_paid ?? 0)} ل.س`}
              subtitle="Total SYP awarded to referrers"
              icon={Banknote}
              color="green"
            />
          </div>

          {/* ── Referral Tree ── */}
          <div className="glass rounded-xl border border-border p-6">
            {/* Section header + search */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-brand-primary" />
                <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-widest">
                  Referral Tree
                </h2>
                <span className="ml-2 bg-brand-primary/20 text-brand-primary text-xs font-semibold px-2 py-0.5 rounded-full">
                  {tree.length}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  id="referral-search"
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search by user ID…"
                  className="w-48 bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary transition-colors"
                />
                <button
                  onClick={refetch}
                  className="p-2 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors"
                  title="Refresh"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>

            {/* Cards */}
            {filtered.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="space-y-4">
                {filtered.map(referrer => (
                  <ReferrerCard key={referrer.referrer_id} referrer={referrer} />
                ))}
              </div>
            )}
          </div>

        </div>
      )}
    </AppLayout>
  );
}
