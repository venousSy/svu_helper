import { useAuth } from '../../contexts/AuthContext';
import { LogOut } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Header({ title }) {
  const { logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-8 py-4 border-b border-border bg-bg-base/70 backdrop-blur-[24px] shrink-0 shadow-sm">
      <motion.h1 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="text-xl font-bold text-text-primary"
      >
        {title}
      </motion.h1>

      <button
        onClick={logout}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors duration-normal"
      >
        <LogOut size={16} />
        Sign Out
      </button>
    </header>
  );
}
