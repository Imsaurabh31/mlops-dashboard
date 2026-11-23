/**
 * React hooks for backend API integration.
 *
 * useApiData   — one-shot fetch with loading/error state
 * usePolling   — repeated fetch on an interval
 * useJobLogs   — polls /training/jobs/{id}/logs until job is done
 * useSSEJob    — Server-Sent Events stream for real-time training metrics
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { trainingApi } from './client';

const TERMINAL = new Set(['completed', 'failed', 'cancelled']);

/**
 * One-shot fetch.
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
 */
export function usePolling(fetcher, interval = 2000, enabled = true) {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);
  const fetcherRef        = useRef(fetcher);
  fetcherRef.current      = fetcher;

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

    run();
    const id = setInterval(run, interval);
    return () => { cancelled = true; clearInterval(id); };
  }, [interval, enabled]);

  return { data, error };
}

/**
 * Poll job logs until the job reaches a terminal state.
 * Falls back gracefully if the backend is unreachable.
 */
export function useJobLogs(jobId, enabled = true) {
  const [logs, setLogs]       = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [status, setStatus]   = useState(null);
  const [epoch, setEpoch]     = useState(0);

  const { data } = usePolling(
    () => trainingApi.getLogs(jobId),
    1500,
    enabled && !!jobId,
  );

  useEffect(() => {
    if (!data) return;
    setLogs(data.logs       ?? []);
    setMetrics(data.metrics ?? []);
    setStatus(data.status   ?? null);
    setEpoch(data.epoch     ?? 0);
  }, [data]);

  return { logs, metrics, status, epoch, isDone: status ? TERMINAL.has(status) : false };
}

/**
 * useSSEJob — Server-Sent Events hook for real-time training updates.
 *
 * Connects to GET /api/training/jobs/{jobId}/stream
 * Receives events: metric | log | status | done
 * Automatically closes the connection when the job finishes.
 * Falls back to polling if SSE is not supported or fails.
 *
 * @param {string}  jobId   — job ID to stream
 * @param {boolean} enabled — only connect when true
 */
export function useSSEJob(jobId, enabled = true) {
  const [metrics, setMetrics]         = useState([]);
  const [logs, setLogs]               = useState([]);
  const [status, setStatus]           = useState(null);
  const [epoch, setEpoch]             = useState(0);
  const [finalAccuracy, setFinal]     = useState(null);
  const [thresholdMet, setThreshold]  = useState(false);
  const [connected, setConnected]     = useState(false);
  const [error, setError]             = useState(null);

  const esRef        = useRef(null);
  const retryTimer   = useRef(null);
  const retryCount   = useRef(0);
  const MAX_RETRIES  = 5;

  useEffect(() => {
    if (!enabled || !jobId) return;

    esRef.current?.close();
    clearTimeout(retryTimer.current);
    retryCount.current = 0;

    const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
    const url  = `${BASE}/training/jobs/${jobId}/stream`;

    function connect() {
      let es;
      try {
        es = new EventSource(url);
        esRef.current = es;
      } catch {
        setError('SSE not supported in this browser');
        return;
      }

      es.onopen = () => {
        setConnected(true);
        setError(null);
        retryCount.current = 0;
      };

      /* Retry with backoff on error instead of permanent close */
      es.onerror = () => {
        setConnected(false);
        es.close();
        if (retryCount.current < MAX_RETRIES) {
          const delay = Math.min(1000 * 2 ** retryCount.current, 10000);
          retryCount.current++;
          setError(`Reconnecting… (attempt ${retryCount.current})`);
          retryTimer.current = setTimeout(connect, delay);
        } else {
          setError('Stream unavailable — job may have completed or backend is unreachable');
        }
      };

      es.addEventListener('metric', (e) => {
        const m = JSON.parse(e.data);
        setMetrics(prev => {
          const idx = prev.findIndex(x => x.epoch === m.epoch);
          if (idx >= 0) { const copy = [...prev]; copy[idx] = m; return copy; }
          return [...prev, m];
        });
        setEpoch(m.epoch);
      });

      es.addEventListener('log', (e) => {
        const { line } = JSON.parse(e.data);
        setLogs(prev => prev.includes(line) ? prev : [...prev, line]);
      });

      es.addEventListener('status', (e) => {
        const d = JSON.parse(e.data);
        setStatus(d.status);
        if (d.epoch          !== undefined) setEpoch(d.epoch);
        if (d.final_accuracy !== undefined) setFinal(d.final_accuracy);
        if (d.threshold_met  !== undefined) setThreshold(d.threshold_met);
      });

      es.addEventListener('done', (e) => {
        const d = JSON.parse(e.data);
        setStatus(d.status ?? 'completed');
        if (d.final_accuracy !== undefined) setFinal(d.final_accuracy);
        if (d.threshold_met  !== undefined) setThreshold(d.threshold_met);
        setConnected(false);
        setError(null);
        es.close();
      });
    }

    connect();

    return () => {
      esRef.current?.close();
      esRef.current = null;
      clearTimeout(retryTimer.current);
      setConnected(false);
    };
  }, [jobId, enabled]);

  return {
    metrics, logs, status, epoch,
    finalAccuracy, thresholdMet,
    connected, error,
    isDone: status ? TERMINAL.has(status) : false,
  };
}
