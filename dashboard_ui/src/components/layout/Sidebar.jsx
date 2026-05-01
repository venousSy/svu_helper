import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderKanban } from 'lucide-react';

const navLinks = [
  { to: '/', icon: LayoutDashboard, label: 'Overview' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
];

export default function Sidebar() {
  return (
    <aside className="flex flex-col w-64 min-h-screen bg-surface/80 backdrop-blur-xl border-r border-border shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-border">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-brand-primary">
          <svg className="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-bold text-text-primary tracking-tight">SVU Helper</p>
          <p className="text-xs text-text-secondary">Admin Dashboard</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navLinks.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-fast ${
                isActive
                  ? 'bg-brand-primary text-text-primary shadow-lg'
                  : 'text-text-secondary hover:bg-surface-elevated hover:text-text-primary'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer tag */}
      <div className="px-6 py-4 border-t border-border">
        <p className="text-xs text-text-muted">v1.0.0</p>
      </div>
    </aside>
  );
}
