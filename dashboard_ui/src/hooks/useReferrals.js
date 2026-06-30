import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

export function useReferrals() {
  const [summary, setSummary] = useState(null);
  const [tree, setTree] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReferrals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryRes, treeRes] = await Promise.all([
        apiClient.get('/referrals/summary'),
        apiClient.get('/referrals/tree'),
      ]);
      setSummary(summaryRes.data);
      setTree(treeRes.data);
    } catch (err) {
      setError('Failed to load referral data.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReferrals();
  }, [fetchReferrals]);

  return { summary, tree, isLoading, error, refetch: fetchReferrals };
}
