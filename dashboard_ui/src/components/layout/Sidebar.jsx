import { NavLink, Link } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, GitBranch, Banknote } from 'lucide-react';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import apiClient from '../../api/client';

const navLinks = [
  { to: '/', icon: LayoutDashboard, label: 'Overview' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/referrals', icon: GitBranch, label: 'Referrals' },
  { to: '/withdrawals', icon: Banknote, label: 'Withdrawals' },
];

export default function Sidebar() {
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    // Fetch pending withdrawal count for sidebar badge
    apiClient.get('/withdrawals/stats')
      .then(res => setPendingCount(res.data.pending_count || 0))
      .catch(() => {});
    // Refresh every 60 seconds
    const id = setInterval(() => {
      apiClient.get('/withdrawals/stats')
        .then(res => setPendingCount(res.data.pending_count || 0))
        .catch(() => {});
    }, 60_000);
    return () => clearInterval(id);
  }, []);

  return (
    <aside className="flex flex-col w-[var(--sidebar-width)] min-h-screen bg-surface/80 backdrop-blur-xl border-r border-border shrink-0 relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-brand-primary/5 to-transparent pointer-events-none" />

      {/* Brand */}
      <Link to="/" className="flex items-center gap-3 px-6 py-6 border-b border-border hover:bg-surface-elevated/50 transition-colors cursor-pointer group z-10">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-brand-primary group-hover:shadow-[0_0_15px_rgba(139,92,246,0.6)] transition-shadow">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-bold text-text-primary tracking-tight">SVU Helper</p>
          <p className="text-xs text-text-secondary">Admin Dashboard</p>
        </div>
      </Link>

      {/* Nav */}
      <nav className="flex-1 px-4 py-6 space-y-2 z-10">
        {navLinks.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              `relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 bg-brand-primary rounded-xl shadow-[0_4px_20px_rgba(139,92,246,0.4)]"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <Icon size={18} className="relative z-10" />
                <span className="relative z-10 flex-1">{label}</span>
                {/* Pending badge on Withdrawals link */}
                {label === 'Withdrawals' && pendingCount > 0 && (
                  <span className="relative z-10 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center animate-pulse">
                    {pendingCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer tag */}
      <div className="px-6 py-4 border-t border-border z-10">
        <p className="text-xs font-medium text-text-muted">v1.1.0 Premium</p>
      </div>
    </aside>
  );
}
