/**
 * SSELivePanel — real-time training panel using Server-Sent Events.
 *
 * Connects to GET /api/training/jobs/{jobId}/stream and renders:
 *  - Live metric cards (val_acc, train_acc, val_loss, train_loss, epoch, progress)
 *  - Animated accuracy and loss charts updating per epoch
 *  - Scrolling terminal log with color-coded lines
 *  - Connected / disconnected indicator
 *
 * Falls back gracefully if the backend SSE endpoint is unavailable —
 * shows the last known state without crashing.
 */
import { useEffect, useRef } from 'react';
import { useSSEJob } from '../api/useApi';
import './SSELivePanel.css';

const TOTAL_EPOCHS = 20;

function MiniChart({ data, color, gradId, label }) {
  if (!data || data.length < 2) {
    return (
      <div className="sse-chart-card">
        <span className="sse-chart-title">{label}</span>
        <div className="sse-chart-empty">Waiting for data…</div>
      </div>
    );
  }

  const min  = Math.min(...data);
  const max  = Math.max(...data);
  const rng  = max - min || 1;
  const pts  = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 300;
    const y = 80 - ((v - min) / rng) * 70 - 5;
    return `${x},${y}`;
  });
  const area = `0,80 ${pts.join(' ')} 300,80`;
  const last = data[data.length - 1];

  return (
    <div className="sse-chart-card">
      <span className="sse-chart-title">{label}</span>
      <div className="sse-chart">
        <svg viewBox="0 0 300 80" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0"   />
            </linearGradient>
          </defs>
          <polygon points={area} fill={`url(#${gradId})`} />
          <polyline points={pts.join(' ')} fill="none" stroke={color}
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <span className="sse-chart-val" style={{ color }}>{last}</span>
    </div>
  );
}

export default function SSELivePanel({ model, jobId, onClose }) {
  const logsEndRef = useRef(null);

  const {
    metrics, logs, status, epoch,
    finalAccuracy, thresholdMet,
    connected, error, isDone,
  } = useSSEJob(jobId, !!jobId);

  /* Auto-scroll logs */
  const prevLogLen = useRef(0);
  useEffect(() => {
    if (logs.length > prevLogLen.current) {
      prevLogLen.current = logs.length;
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [logs]);

  if (!model || !jobId) return null;

  const last      = metrics[metrics.length - 1];
  const accData   = metrics.map(d => d.val_acc   ?? d.valAcc);
  const lossData  = metrics.map(d => d.val_loss  ?? d.valLoss);

  const metricCards = [
    { label: 'Val Accuracy',   val: last ? `${last.val_acc   ?? last.valAcc}%`   : '—', color: model.color      },
    { label: 'Train Accuracy', val: last ? `${last.train_acc ?? last.trainAcc}%` : '—', color: '#10b981'        },
    { label: 'Val Loss',       val: last ? (last.val_loss    ?? last.valLoss)     : '—', color: '#f59e0b'        },
    { label: 'Train Loss',     val: last ? (last.train_loss  ?? last.trainLoss)   : '—', color: '#ef4444'        },
    { label: 'Epoch',          val: `${epoch} / ${TOTAL_EPOCHS}`,                        color: '#6366f1'        },
    { label: 'Progress',       val: `${Math.round((epoch / TOTAL_EPOCHS) * 100)}%`,      color: model.color      },
  ];

  return (
    <div className="sse-panel card">
      {/* Header */}
      <div className="sse-panel__hd">
        <div className="sse-panel__hd-left">
          <span className="sse-panel__icon">{model.icon}</span>
          <div>
            <h3 className="sse-panel__title">{model.title} — Live Training</h3>
            <span className="sse-panel__sub">{model.architecture} · {model.totalImages.toLocaleString()} images</span>
          </div>
        </div>
        <div className="sse-panel__hd-right">
          {/* SSE connection indicator */}
          <div className={`sse-panel__conn${connected ? ' sse-panel__conn--live' : ''}`}>
            <span className={`sse-panel__conn-dot${connected ? ' sse-panel__conn-dot--live' : ''}`} />
            {connected ? 'Live Stream' : isDone ? 'Complete' : 'Connecting…'}
          </div>

          {/* Status badge */}
          {status === 'running' && (
            <span className="badge badge--blue">
              <span className="trn__pulse" style={{ marginRight: 4 }} />
              Epoch {epoch}/{TOTAL_EPOCHS}
            </span>
          )}
          {isDone && (
            <span className={`badge badge--${thresholdMet ? 'green' : 'yellow'}`}>
              {thresholdMet ? `✓ ${finalAccuracy}%` : `⚠ ${finalAccuracy}%`}
            </span>
          )}

          {error && <span className="badge badge--red" title={error}>⚠ {error}</span>}

          <button className="btn btn--ghost btn--sm" onClick={onClose}>✕ Close</button>
        </div>
      </div>

      <div className="sse-panel__body">
        {/* Metric cards */}
        <div className="sse-panel__metrics">
          {metricCards.map(c => (
            <div key={c.label} className="sse-panel__metric-card">
              <span className="sse-panel__metric-val" style={{ color: c.color }}>{c.val}</span>
              <span className="sse-panel__metric-label">{c.label}</span>
            </div>
          ))}
        </div>

        {/* Epoch progress bar */}
        {status === 'running' && (
          <div className="sse-panel__epoch-bar">
            <div className="sse-panel__epoch-label">
              <span>Epoch progress</span>
              <span>{Math.round((epoch / TOTAL_EPOCHS) * 100)}%</span>
            </div>
            <div className="progress-bar-wrap">
              <div className="progress-bar" style={{
                width: `${(epoch / TOTAL_EPOCHS) * 100}%`,
                background: model.color,
                transition: 'width 0.5s ease',
              }} />
            </div>
          </div>
        )}

        {/* Threshold banner */}
        {isDone && (
          <div className={`sse-panel__threshold${thresholdMet ? ' sse-panel__threshold--met' : ' sse-panel__threshold--miss'}`}>
            {thresholdMet
              ? `✅ Accuracy threshold met (${model.threshold}%). Ready for deployment.`
              : `⚠️ Accuracy ${finalAccuracy}% is below threshold (${model.threshold}%). Review required.`}
          </div>
        )}

        {/* Charts */}
        <div className="sse-panel__charts">
          <MiniChart data={accData}  color={model.color} gradId={`acc-${model.id}`}  label="Validation Accuracy" />
          <MiniChart data={lossData} color="#ef4444"     gradId={`loss-${model.id}`} label="Validation Loss"     />
        </div>

        {/* Terminal logs */}
        <div className="sse-panel__logs-wrap">
          <div className="sse-panel__logs-hd">
            <span className="sse-panel__logs-title">📋 Training Logs</span>
            {connected && (
              <span className="badge badge--blue">
                <span className="trn__pulse" style={{ marginRight: 4 }} />Live
              </span>
            )}
          </div>
          <div className="sse-panel__logs" role="log" aria-live="polite">
            {logs.map((line, i) => (
              <div key={i} className={`sse-panel__log-line${
                line.includes('✅')       ? ' sse-panel__log-line--success' :
                line.includes('⚠️')       ? ' sse-panel__log-line--warn'    :
                line.includes('Starting') ? ' sse-panel__log-line--info'    :
                line.includes('❌')       ? ' sse-panel__log-line--error'   : ''
              }`}>
                {line}
              </div>
            ))}
            {logs.length === 0 && (
              <div className="sse-panel__log-line" style={{ color: '#4a5568' }}>
                Waiting for training to start…
              </div>
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
