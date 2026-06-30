import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '../api/client';

const WS_URL = (() => {
  const base = (import.meta.env.VITE_API_URL || window.location.origin).replace(/^http/, 'ws');
  return `${base}/ws/withdrawals`;
})();

export function useWithdrawals(statusFilter = null) {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState({ pending_count: 0, rejected_count: 0, total_paid_syp: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const [listRes, statsRes] = await Promise.all([
        apiClient.get('/withdrawals', { params }),
        apiClient.get('/withdrawals/stats'),
      ]);
      setRequests(listRes.data);
      setStats(statsRes.data);
    } catch (err) {
      setError('Failed to load withdrawal requests.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  // WebSocket for live updates
  useEffect(() => {
    const token = localStorage.getItem('token');
    const ws = new WebSocket(`${WS_URL}?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === 'withdrawal_updated') {
          // Update the specific request's status in local state
          setRequests(prev =>
            prev.map(r =>
              r.request_id === data.id ? { ...r, status: data.status } : r
            )
          );
          // Refresh stats silently
          apiClient.get('/withdrawals/stats')
            .then(res => setStats(res.data))
            .catch(() => {});
        }
      } catch (_) {}
    };

    ws.onerror = () => {}; // Silently ignore WS errors (API still works via polling)

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const markPaid = useCallback(async (requestId, shamcashRef = null) => {
    // Optimistic update
    setRequests(prev =>
      prev.map(r => r.request_id === requestId ? { ...r, status: 'processed', _pending: true } : r)
    );
    try {
      await apiClient.post(`/withdrawals/${requestId}/mark-paid`, {
        shamcash_ref: shamcashRef || null,
      });
      // Refresh stats
      const statsRes = await apiClient.get('/withdrawals/stats');
      setStats(statsRes.data);
    } catch (err) {
      // Roll back optimistic update
      setRequests(prev =>
        prev.map(r => r.request_id === requestId ? { ...r, status: 'pending', _pending: false } : r)
      );
      const detail = err.response?.data?.detail || 'Unknown error';
      throw new Error(detail);
    }
  }, []);

  const rejectRequest = useCallback(async (requestId) => {
    setRequests(prev =>
      prev.map(r => r.request_id === requestId ? { ...r, status: 'rejected', _pending: true } : r)
    );
    try {
      await apiClient.post(`/withdrawals/${requestId}/reject`);
      const statsRes = await apiClient.get('/withdrawals/stats');
      setStats(statsRes.data);
    } catch (err) {
      setRequests(prev =>
        prev.map(r => r.request_id === requestId ? { ...r, status: 'pending', _pending: false } : r)
      );
      const detail = err.response?.data?.detail || 'Unknown error';
      throw new Error(detail);
    }
  }, []);

  return { requests, stats, isLoading, error, refetch: fetchData, markPaid, rejectRequest };
}
