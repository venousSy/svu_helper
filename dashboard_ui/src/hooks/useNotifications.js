import { useState, useEffect, useRef } from 'react';

const WS_URL = (() => {
  const base = (import.meta.env.VITE_API_URL || window.location.origin).replace(/^http/, 'ws');
  return `${base}/ws/notifications`;
})();

export function useNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type !== 'ping') {
            setNotifications(prev => [data, ...prev].slice(0, 50)); // Keep last 50
            setUnreadCount(prev => prev + 1);
        }
      } catch (_) {}
    };

    ws.onerror = () => {}; 

    return () => {
      ws.close();
    };
  }, []);

  const markAllAsRead = () => {
    setUnreadCount(0);
  };

  const clearNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  return { notifications, unreadCount, markAllAsRead, clearNotifications };
}
