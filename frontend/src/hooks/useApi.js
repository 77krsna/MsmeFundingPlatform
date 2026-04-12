// src/hooks/useApi.js
import { useState, useEffect, useCallback } from 'react';

export function useApi(apiFunction, autoFetch = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFunction(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
      return null;
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [autoFetch, fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function usePolling(apiFunction, intervalMs = 30000) {
  const { data, loading, error, refetch } = useApi(apiFunction, true);

  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [refetch, intervalMs]);

  return { data, loading, error, refetch };
}