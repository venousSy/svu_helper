import { NavLink, Link } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, GitBranch, Banknote, ChevronLeft, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
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
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    apiClient.get('/withdrawals/stats')
      .then(res => setPendingCount(res.data.pending_count || 0))
      .catch(() => {});
    const id = setInterval(() => {
      apiClient.get('/withdrawals/stats')
        .then(res => setPendingCount(res.data.pending_count || 0))
        .catch(() => {});
    }, 60_000);
    return () => clearInterval(id);
  }, []);

  return (
    <motion.aside 
      animate={{ width: isCollapsed ? 80 : 272 }} // 272px is 17rem
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="flex flex-col min-h-screen bg-surface/80 backdrop-blur-xl border-r border-border shrink-0 relative z-50"
    >
      <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-brand-primary/5 to-transparent pointer-events-none" />

      <div className="flex items-center justify-between px-6 py-6 border-b border-border z-10 h-[85px] relative">
        <Link to="/" className={`flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer group ${isCollapsed ? 'justify-center w-full' : ''}`}>
          <div className="flex items-center justify-center shrink-0 w-9 h-9 rounded-lg bg-brand-primary group-hover:shadow-[0_0_15px_rgba(139,92,246,0.6)] transition-shadow">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <AnimatePresence>
            {!isCollapsed && (
              <motion.div 
                initial={{ opacity: 0, width: 0 }} 
                animate={{ opacity: 1, width: 'auto' }} 
                exit={{ opacity: 0, width: 0 }}
                className="whitespace-nowrap overflow-hidden"
              >
                <p className="text-sm font-bold text-text-primary tracking-tight">SVU Helper</p>
                <p className="text-xs text-text-secondary">Admin Dashboard</p>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center bg-surface border border-border rounded-full text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors z-50 cursor-pointer shadow-sm hover:shadow"
        >
          {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2 z-10">
        {navLinks.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              `relative flex items-center gap-3 ${isCollapsed ? 'justify-center px-0' : 'px-4'} py-3 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/50'
              }`
            }
            title={isCollapsed ? label : undefined}
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
                <div className="relative z-10 flex items-center justify-center">
                  <Icon size={18} />
                  {label === 'Withdrawals' && pendingCount > 0 && isCollapsed && (
                    <span className="absolute -top-1 -right-2 w-2.5 h-2.5 bg-amber-500 rounded-full border-2 border-surface animate-pulse" />
                  )}
                </div>
                {!isCollapsed && (
                  <span className="relative z-10 flex-1 whitespace-nowrap">{label}</span>
                )}
                {label === 'Withdrawals' && pendingCount > 0 && !isCollapsed && (
                  <span className="relative z-10 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center animate-pulse">
                    {pendingCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border z-10 flex items-center justify-center">
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              exit={{ opacity: 0 }}
              className="text-xs font-medium text-text-muted whitespace-nowrap"
            >
              v1.1.0 Premium
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}
