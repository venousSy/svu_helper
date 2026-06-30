import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, Search, Bell } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNotifications } from '../../hooks/useNotifications';
import NotificationDropdown from './NotificationDropdown';

export default function Header({ title }) {
  const { logout } = useAuth();
  const { notifications, unreadCount, markAllAsRead, clearNotifications } = useNotifications();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleDropdown = () => {
    if (!isDropdownOpen) markAllAsRead();
    setIsDropdownOpen(!isDropdownOpen);
  };

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-8 py-4 border-b border-border bg-bg-base/70 backdrop-blur-[24px] shrink-0 shadow-sm">
      <motion.h1 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="text-xl font-bold text-text-primary hidden md:block"
      >
        {title}
      </motion.h1>

      <div className="flex items-center gap-6 flex-1 justify-end md:justify-between ml-0 md:ml-8">
        {/* Global Search */}
        <div className="relative w-full max-w-md hidden sm:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={16} className="text-text-muted" />
          </div>
          <input
            type="text"
            placeholder="Search projects, students..."
            className="w-full pl-10 pr-4 py-2 bg-surface-elevated border border-border rounded-xl text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-brand-primary/50 focus:ring-4 focus:ring-brand-primary/10 transition-all shadow-sm"
          />
        </div>

        {/* Right side actions */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <button
              onClick={toggleDropdown}
              className="relative p-2 text-text-secondary hover:text-text-primary hover:bg-surface-elevated rounded-lg transition-colors"
            >
              <Bell size={20} />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                </span>
              )}
            </button>
            <AnimatePresence>
              {isDropdownOpen && (
                <NotificationDropdown 
                  notifications={notifications} 
                  onClose={() => setIsDropdownOpen(false)}
                  onClear={clearNotifications}
                />
              )}
            </AnimatePresence>
          </div>

          <button
            onClick={logout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors duration-normal"
          >
            <LogOut size={16} />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </div>
    </header>
  );
}
