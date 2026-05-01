import { useAuth } from '../../contexts/AuthContext';
import { LogOut } from 'lucide-react';

export default function Header({ title }) {
  const { logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-8 py-4 border-b border-border bg-surface-base/50 backdrop-blur-md shrink-0">
      <h1 className="text-xl font-semibold text-text-primary">{title}</h1>

      <button
        onClick={logout}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-all duration-fast"
      >
        <LogOut size={16} />
        Sign Out
      </button>
    </header>
  );
}
