import { useState, useEffect, useRef, useCallback } from 'react';
import './Training.css';

/* ── Model definitions ── */
const MODELS = [
  {
    id: 'gender', title: 'Gender Classification', icon: '👤',
    color: 'var(--accent-blue)', colorLight: 'var(--accent-blue-light)',
    classes: ['Male', 'Female'], totalImages: 9312,
    targetAccuracy: 92.4, architecture: 'ResNet-50', threshold: 90,
  },
  {
    id: 'age', title: 'Age Classification', icon: '📅',
    color: 'var(--accent-purple)', colorLight: 'var(--accent-purple-light)',
    classes: ['Infant', 'Child', 'Teen', 'Adult', 'Mature'], totalImages: 9312,
    targetAccuracy: 87.3, architecture: 'EfficientNet-B0', threshold: 85,
  },
  {
    id: 'staff', title: 'Staff Detection', icon: '👔',
    color: 'var(--accent-teal)', colorLight: 'var(--accent-teal-light)',
    classes: ['Staff', 'Customer'], totalImages: 9312,
    targetAccuracy: 95.1, architecture: 'ResNet-34', threshold: 90,
  },
];

const TOTAL_EPOCHS          = 20;
const AUTO_TRIGGER_THRESHOLD = 80;

/* ── Local time formatter — avoids UTC display bug ── */
function localTimestamp() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/* ── Epoch metric simulation ── */
function generateEpochData(epoch, targetAcc) {
  const progress  = epoch / TOTAL_EPOCHS;
  const noise     = () => (Math.random() - 0.5) * 2;
  const trainAcc  = Math.min(99, targetAcc * 0.85 * progress + 40 * (1 - progress) + noise());
  const valAcc    = Math.min(99, targetAcc * progress       + 35 * (1 - progress) + noise());
  const trainLoss = Math.max(0.01, 1.8  * (1 - progress * 0.90) + noise() * 0.05);
  const valLoss   = Math.max(0.05, 2.1  * (1 - progress * 0.85) + noise() * 0.08);
  return {
    epoch,
    trainAcc:  +trainAcc.toFixed(2),
    valAcc:    +valAcc.toFixed(2),
    trainLoss: +trainLoss.toFixed(4),
    valLoss:   +valLoss.toFixed(4),
  };
}

function generateLog(epoch, metrics) {
  const t = new Date().toLocaleTimeString();
  return `[${t}] Epoch ${epoch}/${TOTAL_EPOCHS} — loss: ${metrics.trainLoss} — acc: ${metrics.trainAcc}% — val_loss: ${metrics.valLoss} — val_acc: ${metrics.valAcc}%`;
}

const TABS = ['Training Jobs', 'Experiments', 'Deployed Models'];

const INIT_JOBS = [
  { id: 'JOB-1024', model: 'gender', task: 'Gender Classification', status: 'completed', started: '2026-10-28 09:14', duration: '4m 32s', accuracy: '92.4%' },
  { id: 'JOB-1022', model: 'staff',  task: 'Staff Detection',       status: 'completed', started: '2026-10-27 18:02', duration: '6m 11s', accuracy: '95.1%' },
  { id: 'JOB-1021', model: 'gender', task: 'Gender Classification',  status: 'failed',   started: '2026-10-27 14:30', duration: '1m 03s', accuracy: '—'     },
  { id: 'JOB-1020', model: 'age',    task: 'Age Classification',     status: 'completed', started: '2026-10-26 11:00', duration: '5m 48s', accuracy: '86.9%' },
];

const EXPERIMENTS_DATA = [
  { name: 'gender-v3', model: 'ResNet-50',       dataset: '9.3k', val_acc: '92.4%', date: '2026-10-28', status: 'best'     },
  { name: 'gender-v2', model: 'MobileNet-V2',    dataset: '7.1k', val_acc: '89.1%', date: '2026-10-25', status: 'archived' },
  { name: 'age-v2',    model: 'EfficientNet-B0', dataset: '9.3k', val_acc: '87.3%', date: '2026-10-27', status: 'best'     },
  { name: 'staff-v2',  model: 'ResNet-34',       dataset: '9.3k', val_acc: '95.1%', date: '2026-10-27', status: 'deployed' },
];

const DEPLOYED_DATA = [
  { name: 'gender-v3', endpoint: '/api/infer/gender', latency: '18ms', req: '1.2k/hr', uptime: '99.8%' },
  { name: 'staff-v2',  endpoint: '/api/infer/staff',  latency: '22ms', req: '1.2k/hr', uptime: '99.9%' },
  { name: 'age-v2',    endpoint: '/api/infer/age',    latency: '25ms', req: '1.2k/hr', uptime: '99.5%' },
];

const JOB_BADGE = { completed: 'green', running: 'blue', failed: 'red', done: 'green' };
const EXP_BADGE = { best: 'green', archived: 'gray', deployed: 'purple' };

/* ── Mini sparkline ── */
function Sparkline({ data, color, width = 120, height = 40 }) {
  if (!data || data.length < 2) return null;
  const min   = Math.min(...data);
  const max   = Math.max(...data);
  const range = max - min || 1;
  const pts   = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 6) - 3;
    return `${x},${y}`;
  }).join(' ');
  const last  = pts.split(' ').pop().split(',');
  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx={last[0]} cy={last[1]} r="3" fill={color}/>
    </svg>
  );
}

export default function Training() {
  const [tab, setTab]               = useState('Training Jobs');
  const [jobs, setJobs]             = useState(INIT_JOBS);
  const [trainingState, setTrainingState] = useState({});
  const [activeModel, setActiveModel]     = useState(null);
  const [autoTriggered, setAutoTriggered] = useState(false);
  const [notification, setNotification]   = useState(null);
  const [curatedPct, setCuratedPct]       = useState(21);

  /* ── Refs — avoid stale closures ── */
  const jobCounterRef       = useRef(1025);
  const intervalsRef        = useRef({});
  const triggerTimeoutsRef  = useRef([]);
  const trainingStateRef    = useRef({});
  const prevLogsLenRef      = useRef({});
  const logsEndRef          = useRef(null);

  /* Keep trainingStateRef in sync */
  useEffect(() => { trainingStateRef.current = trainingState; }, [trainingState]);

  /* ── Auto-trigger simulation ── */
  useEffect(() => {
    if (autoTriggered) return;
    const t = setInterval(() => {
      setCuratedPct(p => {
        if (p >= AUTO_TRIGGER_THRESHOLD) { clearInterval(t); return p; }
        return Math.min(AUTO_TRIGGER_THRESHOLD, p + 0.5);
      });
    }, 300);
    return () => clearInterval(t);
  }, [autoTriggered]);

  useEffect(() => {
    if (curatedPct >= AUTO_TRIGGER_THRESHOLD && !autoTriggered) {
      setAutoTriggered(true);
      showNotification('🚀 Auto-training triggered! Curated images reached 80% threshold.', 'info');
      triggerTimeoutsRef.current.push(
        setTimeout(() => startTraining('gender'), 1000),
        setTimeout(() => startTraining('age'),    2000),
        setTimeout(() => startTraining('staff'),  3000),
      );
    }
  }, [curatedPct, autoTriggered]); // eslint-disable-line

  /* ── Cleanup on unmount ── */
  useEffect(() => () => {
    Object.values(intervalsRef.current).forEach(clearInterval);
    triggerTimeoutsRef.current.forEach(clearTimeout);
  }, []);

  /* ── Log scroll ── */
  useEffect(() => {
    if (!activeModel) return;
    const st = trainingState[activeModel];
    if (!st?.logs) return;
    const prev = prevLogsLenRef.current[activeModel] || 0;
    if (st.logs.length > prev) {
      prevLogsLenRef.current[activeModel] = st.logs.length;
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [trainingState, activeModel]);

  const showNotification = (msg, type = 'info') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 5000);
  };

  /* ── startTraining ── */
  const startTraining = useCallback((modelId) => {
    const model = MODELS.find(m => m.id === modelId);
    if (!model) return;

    /* Issue 4 fix: read from ref — never stale */
    if (intervalsRef.current[modelId]) return; // interval already running
    if (trainingStateRef.current[modelId]?.status === 'running') return;

    const jobId     = `JOB-${jobCounterRef.current++}`;
    const startedAt = localTimestamp();   /* Issue 5 fix: local time */
    const trainStart = Date.now();

    setJobs(prev => [{
      id: jobId, model: modelId, task: model.title,
      status: 'running', started: startedAt, duration: '—', accuracy: '—',
    }, ...prev]);

    const initLogs = [
      `[${new Date().toLocaleTimeString()}] Starting ${model.title} training…`,
      `[${new Date().toLocaleTimeString()}] Architecture: ${model.architecture}`,
      `[${new Date().toLocaleTimeString()}] Dataset: ${model.totalImages.toLocaleString()} images, ${model.classes.length} classes`,
    ];

    setTrainingState(prev => ({
      ...prev,
      [modelId]: { status: 'running', epoch: 0, metrics: [], logs: initLogs, jobId },
    }));

    setActiveModel(modelId);

    /* Run epochs */
    let epoch = 0;
    const interval = setInterval(() => {
      epoch++;
      const metrics = generateEpochData(epoch, model.targetAccuracy);
      const log     = generateLog(epoch, metrics);

      setTrainingState(prev => {
        const cur = prev[modelId] || {};
        const newMetrics = [...(cur.metrics || []), metrics];
        const newLogs    = [...(cur.logs    || []), log];
        const isDone     = epoch >= TOTAL_EPOCHS;

        if (isDone) {
          /* Issue 3 fix: read finalAcc from the last entry in newMetrics, not a fresh random call */
          const finalAcc  = newMetrics[newMetrics.length - 1].valAcc;
          const exceeded  = finalAcc >= model.threshold;
          /* Measured duration — not a constant */
          const durationMs = Date.now() - trainStart;
          const durationS  = (durationMs / 1000).toFixed(0);

          /* Update job row — failed threshold → distinct status */
          setJobs(jPrev => jPrev.map(j =>
            j.id === jobId
              ? { ...j, status: exceeded ? 'completed' : 'failed', duration: `${durationS}s`, accuracy: `${finalAcc}%` }
              : j
          ));

          showNotification(
            exceeded
              ? `✅ ${model.title} trained — ${finalAcc}% accuracy. Ready to deploy!`
              : `⚠️ ${model.title} training complete — ${finalAcc}% (below threshold)`,
            exceeded ? 'success' : 'warning'
          );

          /* Clear interval outside the updater to avoid side effects in setState */
          setTimeout(() => {
            clearInterval(interval);
            delete intervalsRef.current[modelId];
          }, 0);

          return {
            ...prev,
            [modelId]: {
              ...cur,
              epoch,
              metrics:       newMetrics,
              status:        'done',
              finalAccuracy: finalAcc,
              thresholdMet:  exceeded,
              logs: [...newLogs,
                `[${new Date().toLocaleTimeString()}] Training complete! Final val_acc: ${finalAcc}%`,
                exceeded
                  ? `[${new Date().toLocaleTimeString()}] ✅ Accuracy threshold met (${model.threshold}%). Ready for deployment.`
                  : `[${new Date().toLocaleTimeString()}] ⚠️ Accuracy below threshold (${model.threshold}%). Review required.`,
              ],
            },
          };
        }

        return {
          ...prev,
          [modelId]: { ...cur, epoch, metrics: newMetrics, logs: newLogs, status: 'running' },
        };
      });
    }, 600);

    intervalsRef.current[modelId] = interval;
  }, []); // stable — uses only refs and closures over consts

  const getState = (id) => trainingState[id] || { status: 'idle', epoch: 0, metrics: [], logs: [] };

  return (
    <div className="trn">

      {/* ── Notification ── */}
      {notification && (
        <div className={`trn-notif trn-notif--${notification.type}`}>
          <span>{notification.msg}</span>
          <button onClick={() => setNotification(null)}>✕</button>
        </div>
      )}

      {/* ── Auto-trigger bar ── */}
      {!autoTriggered ? (
        <div className="trn-autotrigger card">
          <div className="trn-autotrigger__left">
            <span className="trn-autotrigger__title">⚡ Auto-Training Monitor</span>
            <span className="trn-autotrigger__sub">
              Training auto-triggers when curated images reach {AUTO_TRIGGER_THRESHOLD}%
            </span>
          </div>
          <div className="trn-autotrigger__right">
            <div className="trn-autotrigger__pct-row">
              <span className="trn-autotrigger__label">Curation progress</span>
              <span className="trn-autotrigger__pct">{curatedPct.toFixed(1)}%</span>
              <span className="trn-autotrigger__target">/ {AUTO_TRIGGER_THRESHOLD}%</span>
            </div>
            <div className="progress-bar-wrap">
              <div className="progress-bar trn-autotrigger__bar"
                style={{ width: `${(curatedPct / AUTO_TRIGGER_THRESHOLD) * 100}%` }}/>
            </div>
          </div>
          <button className="btn btn--primary btn--sm"
            onClick={() => setCuratedPct(AUTO_TRIGGER_THRESHOLD)}>
            Simulate Trigger
          </button>
        </div>
      ) : (
        <div className="trn-autotrigger card trn-autotrigger--triggered">
          <span>⚡ Auto-training triggered at {AUTO_TRIGGER_THRESHOLD}% curation threshold</span>
          <span className="badge badge--green">Active</span>
        </div>
      )}

      {/* ── Model cards ── */}
      <div className="trn__cards">
        {MODELS.map(m => {
          const st         = getState(m.id);
          const lastMetric = st.metrics?.[st.metrics.length - 1];
          const accHistory = st.metrics?.map(d => d.valAcc ?? d.val_acc) || [];

          // Helper to read either camelCase (frontend sim) or snake_case (backend API)
          const valAcc    = lastMetric ? (lastMetric.valAcc  ?? lastMetric.val_acc)  : null;
          const valLoss   = lastMetric ? (lastMetric.valLoss ?? lastMetric.val_loss) : null;

          return (
            <div key={m.id}
              className={`trn-card card${activeModel === m.id ? ' trn-card--active' : ''}`}
              style={{ '--mc': m.color, '--ml': m.colorLight }}>

              <div className="trn-card__hd">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 18 }}>{m.icon}</span>
                  <h3 className="trn-card__title">{m.title}</h3>
                </div>
                <span className={`badge badge--${
                  st.status === 'running' ? 'blue' :
                  st.status === 'done'    ? 'green' :
                  st.status === 'failed'  ? 'red'   : 'yellow'}`}>
                  {st.status === 'running' && <span className="trn__pulse" style={{ marginRight: 4 }}/>}
                  {st.status === 'idle'    ? 'Ready' :
                   st.status === 'running' ? `Epoch ${st.epoch}/${TOTAL_EPOCHS}` :
                   st.status === 'done'    ? `✓ ${st.finalAccuracy ?? m.targetAccuracy}%` : 'Failed'}
                </span>
              </div>

              <div className="trn-card__stats">
                {[
                  { val: valAcc  != null ? `${valAcc}%`  : `${m.targetAccuracy}%`, label: 'Val Acc' },
                  { val: valLoss != null ?  valLoss       : '—',                    label: 'Val Loss' },
                  { val: m.classes.length,                                           label: 'Classes' },
                ].map((s, i) => (
                  <div key={i} style={{ display: 'flex' }}>
                    {i > 0 && <div className="trn-card__divider"/>}
                    <div className="trn-card__stat">
                      <span className="trn-card__stat-val" style={{ color: m.color }}>{s.val}</span>
                      <span className="trn-card__stat-label">{s.label}</span>
                    </div>
                  </div>
                ))}
              </div>

              {accHistory.length > 1 && (
                <div className="trn-card__sparkline">
                  <span className="trn-card__spark-label">Accuracy trend</span>
                  <Sparkline data={accHistory} color={m.color}/>
                </div>
              )}

              {st.status === 'running' && (
                <div>
                  <div className="trn-card__epoch-row">
                    <span className="trn-card__epoch-label">Epoch {st.epoch} / {TOTAL_EPOCHS}</span>
                    <span className="trn-card__epoch-pct">{Math.round((st.epoch / TOTAL_EPOCHS) * 100)}%</span>
                  </div>
                  <div className="progress-bar-wrap">
                    <div className="progress-bar" style={{
                      width: `${(st.epoch / TOTAL_EPOCHS) * 100}%`,
                      background: m.color, transition: 'width 0.5s ease',
                    }}/>
                  </div>
                </div>
              )}

              {st.status === 'done' && st.thresholdMet && (
                <div className="trn-card__threshold-met">✅ Threshold met — ready for deployment</div>
              )}

              <div style={{ display: 'flex', gap: 8 }}>
                {st.status === 'idle' && (
                  <button className="btn trn-card__btn"
                    style={{ background: m.color, color: '#fff', border: 'none', flex: 1, justifyContent: 'center' }}
                    onClick={() => startTraining(m.id)}>
                    Train {m.title.split(' ')[0]} Model
                  </button>
                )}
                {st.status === 'running' && (
                  <button className="btn btn--ghost trn-card__btn"
                    style={{ flex: 1, justifyContent: 'center' }}
                    onClick={() => setActiveModel(m.id)}>
                    View Live Progress
                  </button>
                )}
                {st.status === 'done' && (
                  <>
                    <button className="btn btn--ghost btn--sm"
                      style={{ flex: 1, justifyContent: 'center' }}
                      onClick={() => setActiveModel(m.id)}>
                      View Results
                    </button>
                    {st.thresholdMet && (
                      <button className="btn btn--primary btn--sm"
                        style={{ flex: 1, justifyContent: 'center' }}
                        onClick={() => alert(`Deploy "${m.title}" — Stage 3 will handle this.`)}
                        title="Stage 3 — coming next">
                        🚀 Deploy
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Live Training Panel ── */}
      {activeModel && (() => {
        const m          = MODELS.find(x => x.id === activeModel);
        const st         = getState(activeModel);
        const lastMetric = st.metrics?.[st.metrics.length - 1];
        const accHistory = st.metrics?.map(d => d.valAcc ?? d.val_acc) || [];
        const lossHistory= st.metrics?.map(d => d.valLoss ?? d.val_loss) || [];

        return (
          <div className="trn-live card">
            <div className="trn-live__hd">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 20 }}>{m.icon}</span>
                <div>
                  <h3 className="trn-live__title">{m.title} — Live Training</h3>
                  <span className="trn-live__sub">{m.architecture} · {m.totalImages.toLocaleString()} images</span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {st.status === 'running' && (
                  <span className="badge badge--blue">
                    <span className="trn__pulse" style={{ marginRight: 4 }}/>
                    Epoch {st.epoch}/{TOTAL_EPOCHS}
                  </span>
                )}
                {st.status === 'done' && (
                  <span className="badge badge--green">
                    ✓ {st.finalAccuracy ?? m.targetAccuracy}%
                  </span>
                )}
                <button className="btn btn--ghost btn--sm" onClick={() => setActiveModel(null)}>✕ Close</button>
              </div>
            </div>

            <div className="trn-live__body">
              {/* Metric cards */}
              <div className="trn-live__metrics">
                {[
                  { label: 'Val Accuracy',   value: lastMetric ? `${lastMetric.valAcc}%`   : '—', color: m.color         },
                  { label: 'Train Accuracy', value: lastMetric ? `${lastMetric.trainAcc}%` : '—', color: '#10b981'       },
                  { label: 'Val Loss',       value: lastMetric ?  lastMetric.valLoss        : '—', color: '#f59e0b'       },
                  { label: 'Train Loss',     value: lastMetric ?  lastMetric.trainLoss      : '—', color: '#ef4444'       },
                  { label: 'Epoch',          value: `${st.epoch} / ${TOTAL_EPOCHS}`,                color: '#6366f1'       },
                  { label: 'Progress',       value: `${Math.round((st.epoch / TOTAL_EPOCHS) * 100)}%`, color: m.color    },
                ].map(card => (
                  <div key={card.label} className="trn-live__metric-card">
                    <span className="trn-live__metric-val" style={{ color: card.color }}>{card.value}</span>
                    <span className="trn-live__metric-label">{card.label}</span>
                  </div>
                ))}
              </div>

              {/* Charts */}
              <div className="trn-live__charts">
                {[
                  { title: 'Validation Accuracy', data: accHistory,  color: m.color,  gradId: `acc-${m.id}`  },
                  { title: 'Validation Loss',      data: lossHistory, color: '#ef4444',gradId: `loss-${m.id}` },
                ].map(chart => (
                  <div key={chart.title} className="trn-live__chart-card">
                    <span className="trn-live__chart-title">{chart.title}</span>
                    <div className="trn-live__chart">
                      {chart.data.length > 1 ? (
                        <svg viewBox="0 0 300 80" preserveAspectRatio="none" style={{ width: '100%', height: '100%' }}>
                          <defs>
                            <linearGradient id={chart.gradId} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%"   stopColor={chart.color} stopOpacity="0.3"/>
                              <stop offset="100%" stopColor={chart.color} stopOpacity="0"/>
                            </linearGradient>
                          </defs>
                          {(() => {
                            const min  = Math.min(...chart.data);
                            const max  = Math.max(...chart.data);
                            const rng  = max - min || 1;
                            const pts  = chart.data.map((v, i) => {
                              const x = (i / (chart.data.length - 1)) * 300;
                              const y = 80 - ((v - min) / rng) * 70 - 5;
                              return `${x},${y}`;
                            });
                            return (
                              <>
                                <polygon points={`0,80 ${pts.join(' ')} 300,80`} fill={`url(#${chart.gradId})`}/>
                                <polyline points={pts.join(' ')} fill="none" stroke={chart.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              </>
                            );
                          })()}
                        </svg>
                      ) : (
                        <div className="trn-live__chart-empty">Waiting for data…</div>
                      )}
                    </div>
                    {lastMetric && (
                      <span className="trn-live__chart-val" style={{ color: chart.color }}>
                        {chart.title.includes('Accuracy') ? `${lastMetric.valAcc}%` : lastMetric.valLoss}
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* Logs */}
              <div className="trn-live__logs-wrap">
                <div className="trn-live__logs-hd">
                  <span className="trn-live__logs-title">📋 Training Logs</span>
                  {st.status === 'running' && (
                    <span className="badge badge--blue">
                      <span className="trn__pulse" style={{ marginRight: 4 }}/>Live
                    </span>
                  )}
                </div>
                <div className="trn-live__logs" role="log" aria-live="polite" aria-label="Training log output">
                  {st.logs?.map((line, i) => (
                    <div key={i} className={`trn-live__log-line${
                      line.includes('✅')       ? ' trn-live__log-line--success' :
                      line.includes('⚠️')       ? ' trn-live__log-line--warn'    :
                      line.includes('Starting') ? ' trn-live__log-line--info'    : ''}`}>
                      {line}
                    </div>
                  ))}
                  <div ref={logsEndRef}/>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Tabs ── */}
      <div className="trn__tabs">
        {TABS.map(t => (
          <button key={t}
            className={`trn__tab${tab === t ? ' trn__tab--active' : ''}`}
            onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {/* ── Training Jobs ── */}
      {tab === 'Training Jobs' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="trn__tbl-hd">
            <h3 className="trn__tbl-title">Active &amp; Recent Jobs</h3>
            <button className="btn btn--ghost btn--sm"
              onClick={() => alert('Live refresh requires the backend API.')}
              title="Requires backend">
              ↻ Refresh
            </button>
          </div>
          <table className="tbl">
            <thead><tr>
              <th>JOB ID</th><th>TASK</th><th>STATUS</th><th>STARTED</th><th>DURATION</th><th>ACCURACY</th><th>ACTIONS</th>
            </tr></thead>
            <tbody>
              {jobs.map(j => {
                const jobState = Object.values(trainingState).find(s => s.jobId === j.id);
                return (
                  <tr key={j.id}>
                    <td><code className="trn__code">{j.id}</code></td>
                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{j.task}</td>
                    <td>
                      <span className={`badge badge--${JOB_BADGE[j.status] || 'gray'}`}>
                        {j.status === 'running' && <span className="trn__pulse" style={{ marginRight: 4 }}/>}
                        {j.status.charAt(0).toUpperCase() + j.status.slice(1)}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{j.started}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{j.duration}</td>
                    <td style={{ fontWeight: 700, color: j.accuracy !== '—' ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                      {j.accuracy}
                    </td>
                    <td>
                      <button className="btn btn--ghost btn--sm"
                        onClick={() => {
                          /* Show live panel only if job state exists, else inform */
                          if (jobState) { setActiveModel(j.model); }
                          else alert(`Logs for ${j.id} are not available — historical job data requires the backend API.`);
                        }}>
                        View Logs
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Experiments ── */}
      {tab === 'Experiments' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="trn__tbl-hd"><h3 className="trn__tbl-title">Experiment Tracker</h3></div>
          <table className="tbl">
            <thead><tr><th>EXPERIMENT</th><th>MODEL</th><th>DATASET</th><th>VAL ACCURACY</th><th>DATE</th><th>STATUS</th></tr></thead>
            <tbody>
              {EXPERIMENTS_DATA.map(e => (
                <tr key={e.name}>
                  <td><code className="trn__code">{e.name}</code></td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{e.model}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{e.dataset} images</td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{e.val_acc}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{e.date}</td>
                  <td><span className={`badge badge--${EXP_BADGE[e.status]}`}>{e.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Deployed Models ── */}
      {tab === 'Deployed Models' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="trn__tbl-hd"><h3 className="trn__tbl-title">Live Deployments</h3></div>
          <table className="tbl">
            <thead><tr><th>MODEL</th><th>ENDPOINT</th><th>LATENCY</th><th>REQUESTS</th><th>UPTIME</th><th>ACTIONS</th></tr></thead>
            <tbody>
              {DEPLOYED_DATA.map(d => (
                <tr key={d.name}>
                  <td><code className="trn__code">{d.name}</code></td>
                  <td><span className="chip">🔗 {d.endpoint}</span></td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{d.latency}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{d.req}</td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{d.uptime}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn--ghost btn--sm"
                        onClick={() => alert(`Manage "${d.name}" — available once deployment backend is connected.`)}>
                        Manage
                      </button>
                      <button className="btn btn--danger btn--sm"
                        onClick={() => {
                          if (window.confirm(`Stop "${d.name}"? This will take the endpoint offline.`))
                            alert('Stop endpoint requires the deployment backend.');
                        }}>
                        Stop
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
