import { motion } from 'framer-motion';
import { Bell, Info, CheckCircle, AlertTriangle, Trash2 } from 'lucide-react';

export default function NotificationDropdown({ notifications, onClose, onClear }) {
  const timeAgo = (date) => {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    return "Just now";
  };

  const getIcon = (type) => {
    switch (type) {
      case 'withdrawal_updated':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'withdrawal_created':
        return <Bell size={16} className="text-brand-primary" />;
      default:
        return <Info size={16} className="text-blue-500" />;
    }
  };

  const getMessage = (notif) => {
    switch (notif.type) {
      case 'withdrawal_updated':
        return `Withdrawal request ${notif.id} status updated to ${notif.status}`;
      default:
        return notif.message || 'New notification received';
    }
  };

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.95 }}
        transition={{ duration: 0.15 }}
        className="absolute right-0 top-full mt-2 w-80 max-h-96 overflow-y-auto bg-surface-base border border-border rounded-xl shadow-lg z-50 overflow-hidden flex flex-col"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface-elevated sticky top-0 z-10">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <Bell size={14} />
            Notifications
          </h3>
          {notifications.length > 0 && (
            <button 
              onClick={(e) => { e.stopPropagation(); onClear(); }}
              className="text-xs text-text-muted hover:text-red-400 transition-colors flex items-center gap-1"
            >
              <Trash2 size={12} />
              Clear
            </button>
          )}
        </div>
        
        <div className="flex-1 divide-y divide-border/50">
          {notifications.length === 0 ? (
            <div className="p-8 text-center text-text-muted flex flex-col items-center gap-2">
              <Bell size={24} className="opacity-20" />
              <p className="text-sm">No new notifications</p>
            </div>
          ) : (
            notifications.map((notif, i) => (
              <div key={i} className="px-4 py-3 hover:bg-surface-elevated/50 transition-colors flex gap-3 items-start">
                <div className="mt-0.5 shrink-0">
                  {getIcon(notif.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary text-pretty line-clamp-2">
                    {getMessage(notif)}
                  </p>
                  <p className="text-xs text-text-muted mt-1">
                    {notif.timestamp ? timeAgo(notif.timestamp) : 'Just now'}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </motion.div>
    </>
  );
}
