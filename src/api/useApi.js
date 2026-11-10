/**
 * React hooks for backend API integration.
 *
 * useApiData   — one-shot fetch with loading/error state
 * usePolling   — repeated fetch on an interval
 * useJobLogs   — polls /training/jobs/{id}/logs until job is done
 */
import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * One-shot fetch.
 * @param {Function} fetcher  — async function returning data
 * @param {Array}    deps     — re-fetch when these change
 */
export function useApiData(fetcher, deps = []) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetchData(); }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Poll a fetcher on a fixed interval.
 * @param {Function} fetcher    — async function returning data
 * @param {number}   interval   — ms between polls (default 2000)
 * @param {boolean}  enabled    — pause polling when false
 */
export function usePolling(fetcher, interval = 2000, enabled = true) {
  const [data, setData]       = useState(null);
  const [error, setError]     = useState(null);
  const fetcherRef            = useRef(fetcher);
  fetcherRef.current          = fetcher;

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    const run = async () => {
      try {
        const result = await fetcherRef.current();
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) setError(err.message || 'Poll failed');
      }
    };

    run(); // immediate first call
    const id = setInterval(run, interval);
    return () => { cancelled = true; clearInterval(id); };
  }, [interval, enabled]);

  return { data, error };
}

/**
 * Poll job logs until the job reaches a terminal state.
 * @param {string}   jobId     — job ID to poll
 * @param {boolean}  enabled   — start polling only when true
 */
export function useJobLogs(jobId, enabled = true) {
  const TERMINAL = new Set(['completed', 'failed', 'cancelled']);
  const [logs, setLogs]       = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [status, setStatus]   = useState(null);
  const [epoch, setEpoch]     = useState(0);

  const { data } = usePolling(
    () => import('./client.js').then(m => m.trainingApi.getLogs(jobId)),
    1500,
    enabled && !!jobId,
  );

  useEffect(() => {
    if (!data) return;
    setLogs(data.logs    ?? []);
    setMetrics(data.metrics ?? []);
    setStatus(data.status   ?? null);
    setEpoch(data.epoch     ?? 0);
  }, [data]);

  const isDone = status ? TERMINAL.has(status) : false;

  return { logs, metrics, status, epoch, isDone };
}
