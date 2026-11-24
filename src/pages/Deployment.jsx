import { useState, useEffect } from 'react';
import { deployApi, trainingApi } from '../api/client';
import './Deployment.css';

const HEALTH_COLOR = {
  healthy:  'var(--accent-green)',
  degraded: 'var(--accent-yellow)',
  offline:  'var(--accent-red)',
  archived: 'var(--text-muted)',
};

const STATUS_BADGE = {
  active:   'green',
  archived: 'gray',
  stopped:  'red',
};

const MODEL_ICON = { gender: '👤', age: '📅', staff: '👔' };

const TABS = ['Active Deployments', 'All Versions', 'Audit Log'];

export default function Deployment() {
  const [tab, setTab]           = useState('Active Deployments');
  const [active, setActive]     = useState({});
  const [all, setAll]           = useState([]);
  const [log, setLog]           = useState([]);
  const [summary, setSummary]   = useState(null);
  const [jobs, setJobs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [toast, setToast]       = useState(null);
  const [confirm, setConfirm]   = useState(null); // { type, dep, message }

  /* ── Load data ── */
  const loadAll = async () => {
    setLoading(true);
    try {
      const [act, allDeps, sm, lg, jbs] = await Promise.all([
        deployApi.active(),
        deployApi.list(),
        deployApi.summary(),
        deployApi.log(),
        trainingApi.listJobs(),
      ]);
      setActive(act);
      setAll(allDeps);
      setSummary(sm);
      setLog(lg);
      setJobs(jbs);
    } catch (e) {
      showToast(`Failed to load: ${e.message}`, 'danger');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  /* ── Actions ── */
  const handleDeploy = async (jobId) => {
    try {
      const res = await deployApi.deploy(jobId);
      showToast(`✅ ${res.deployment.task} deployed as ${res.deployment.version}`);
      await loadAll();
    } catch (e) {
      showToast(`❌ Deploy failed: ${e.message}`, 'danger');
    }
    setConfirm(null);
  };

  const handleRollback = async (depId) => {
    try {
      const res = await deployApi.rollback(depId);
      showToast(`↩️ Rolled back to ${res.deployment.version}`);
      await loadAll();
    } catch (e) {
      showToast(`❌ Rollback failed: ${e.message}`, 'danger');
    }
    setConfirm(null);
  };

  const handleStop = async (depId) => {
    try {
      const res = await deployApi.stop(depId);
      showToast(`⏹ ${res.deployment.task} ${res.deployment.version} stopped`, 'warning');
      await loadAll();
    } catch (e) {
      showToast(`❌ Stop failed: ${e.message}`, 'danger');
    }
    setConfirm(null);
  };

  const handleRefreshHealth = async () => {
    try {
      await deployApi.refreshHealth();
      await loadAll();
      showToast('Health refreshed');
    } catch (e) {
      showToast(`❌ ${e.message}`, 'danger');
    }
  };

  /* Jobs eligible for deployment */
  const deployableJobs = jobs.filter(j => j.status === 'completed' && j.threshold_met);

  return (
    <div className="dep">

      {/* ── Toast ── */}
      {toast && (
        <div className={`dep-toast dep-toast--${toast.type}`}>
          {toast.msg}
          <button onClick={() => setToast(null)}>✕</button>
        </div>
      )}

      {/* ── Confirm dialog ── */}
      {confirm && (
        <div className="dep-confirm-overlay" onClick={() => setConfirm(null)}>
          <div className="dep-confirm card" onClick={e => e.stopPropagation()}>
            <h3 className="dep-confirm__title">{confirm.title}</h3>
            <p className="dep-confirm__msg">{confirm.message}</p>
            <div className="dep-confirm__actions">
              <button className="btn btn--ghost" onClick={() => setConfirm(null)}>Cancel</button>
              <button
                className={`btn ${confirm.type === 'stop' ? 'btn--danger' : 'btn--primary'}`}
                onClick={confirm.action}
              >
                {confirm.label}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Summary cards ── */}
      {summary && (
        <div className="dep__summary">
          {[
            { label: 'Active',       value: summary.total_active,   color: 'green',  icon: '🟢' },
            { label: 'Avg Latency',  value: `${summary.avg_latency_ms}ms`, color: 'blue', icon: '⚡' },
            { label: 'Avg Uptime',   value: `${summary.avg_uptime_pct}%`,  color: 'teal', icon: '📈' },
            { label: 'Degraded',     value: summary.degraded,       color: summary.degraded > 0 ? 'yellow' : 'green', icon: '⚠️' },
          ].map(s => (
            <div key={s.label} className={`dep-stat card dep-stat--${s.color}`}>
              <span className="dep-stat__icon">{s.icon}</span>
              <span className="dep-stat__val">{s.value}</span>
              <span className="dep-stat__label">{s.label}</span>
            </div>
          ))}

          <button className="btn btn--ghost dep-stat__refresh" onClick={handleRefreshHealth}>
            ↻ Refresh Health
          </button>
        </div>
      )}

      {/* ── Deployable jobs banner ── */}
      {deployableJobs.length > 0 && (
        <div className="dep-eligible card">
          <div className="dep-eligible__left">
            <span className="dep-eligible__icon">🚀</span>
            <div>
              <span className="dep-eligible__title">
                {deployableJobs.length} model{deployableJobs.length > 1 ? 's' : ''} ready to deploy
              </span>
              <span className="dep-eligible__sub">Training completed and accuracy threshold met</span>
            </div>
          </div>
          <div className="dep-eligible__jobs">
            {deployableJobs.map(j => (
              <button
                key={j.id}
                className="btn btn--primary btn--sm"
                onClick={() => setConfirm({
                  title:   `Deploy ${j.task}`,
                  message: `Deploy ${j.id} (accuracy ${j.accuracy}) to production?`,
                  label:   '🚀 Deploy',
                  type:    'deploy',
                  action:  () => handleDeploy(j.id),
                })}
              >
                {MODEL_ICON[j.model]} Deploy {j.task.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Tabs ── */}
      <div className="dep__tabs">
        {TABS.map(t => (
          <button
            key={t}
            className={`dep__tab${tab === t ? ' dep__tab--active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t}
            {t === 'Active Deployments' && summary && (
              <span className="dep__tab-badge">{summary.total_active}</span>
            )}
          </button>
        ))}
      </div>

      {/* ══ TAB: Active Deployments ══ */}
      {tab === 'Active Deployments' && (
        <div className="dep__cards">
          {['gender', 'age', 'staff'].map(model => {
            const dep = active[model];
            return (
              <div key={model} className={`dep-card card${dep ? ' dep-card--active' : ''}`}>
                <div className="dep-card__hd">
                  <div className="dep-card__hd-left">
                    <span className="dep-card__icon">{MODEL_ICON[model]}</span>
                    <div>
                      <h3 className="dep-card__title">
                        {dep ? dep.task : `${model.charAt(0).toUpperCase() + model.slice(1)} Classification`}
                      </h3>
                      {dep && <span className="dep-card__version">{dep.version}</span>}
                    </div>
                  </div>
                  {dep ? (
                    <div
                      className="dep-card__health"
                      style={{ color: HEALTH_COLOR[dep.health] }}
                    >
                      <span className="dep-card__health-dot" style={{ background: HEALTH_COLOR[dep.health] }} />
                      {dep.health}
                    </div>
                  ) : (
                    <span className="badge badge--gray">Not deployed</span>
                  )}
                </div>

                {dep ? (
                  <>
                    <div className="dep-card__metrics">
                      {[
                        { label: 'Accuracy',   val: `${dep.accuracy}%`,       color: 'var(--accent-green)'  },
                        { label: 'Latency',    val: `${dep.latency_ms}ms`,    color: 'var(--accent-blue)'   },
                        { label: 'Req/hr',     val: dep.requests_hr,          color: 'var(--accent-purple)' },
                        { label: 'Uptime',     val: `${dep.uptime_pct}%`,     color: 'var(--accent-teal)'   },
                      ].map(m => (
                        <div key={m.label} className="dep-card__metric">
                          <span className="dep-card__metric-val" style={{ color: m.color }}>{m.val}</span>
                          <span className="dep-card__metric-label">{m.label}</span>
                        </div>
                      ))}
                    </div>

                    <div className="dep-card__endpoint">
                      <span className="chip">🔗 {dep.endpoint}</span>
                    </div>

                    <div className="dep-card__meta">
                      <span>Deployed {dep.deployed_at}</span>
                      <span>by {dep.deployed_by}</span>
                      <span>Job: {dep.job_id}</span>
                    </div>

                    <div className="dep-card__actions">
                      {dep.rollback_to && (
                        <button
                          className="btn btn--ghost btn--sm"
                          onClick={() => setConfirm({
                            title:   `Rollback ${dep.task}`,
                            message: `Roll back ${dep.task} from ${dep.version} to the previous version?`,
                            label:   '↩️ Rollback',
                            type:    'rollback',
                            action:  () => handleRollback(dep.id),
                          })}
                        >
                          ↩ Rollback
                        </button>
                      )}
                      <button
                        className="btn btn--danger btn--sm"
                        onClick={() => setConfirm({
                          title:   `Stop ${dep.task}`,
                          message: `Stop ${dep.version} of ${dep.task}? This takes the endpoint offline.`,
                          label:   '⏹ Stop',
                          type:    'stop',
                          action:  () => handleStop(dep.id),
                        })}
                      >
                        ⏹ Stop
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="dep-card__empty">
                    <p>No active deployment</p>
                    <p className="dep-card__empty-hint">Train a model and deploy it to activate this endpoint</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ══ TAB: All Versions ══ */}
      {tab === 'All Versions' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="dep__tbl-hd">
            <h3 className="dep__tbl-title">All Deployment Versions</h3>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{all.length} total</span>
          </div>
          <table className="tbl">
            <thead>
              <tr>
                <th>ID</th><th>MODEL</th><th>VERSION</th><th>JOB</th>
                <th>ACCURACY</th><th>DEPLOYED AT</th><th>STATUS</th><th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {all.map(d => (
                <tr key={d.id}>
                  <td><code style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{d.id}</code></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>{MODEL_ICON[d.model]}</span>
                      <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{d.task}</span>
                    </div>
                  </td>
                  <td><span className="badge badge--blue">{d.version}</span></td>
                  <td><code style={{ fontSize: 11 }}>{d.job_id}</code></td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{d.accuracy}%</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{d.deployed_at}</td>
                  <td><span className={`badge badge--${STATUS_BADGE[d.status] || 'gray'}`}>{d.status}</span></td>
                  <td>
                    {d.status === 'active' && d.rollback_to && (
                      <button className="btn btn--ghost btn--sm"
                        onClick={() => setConfirm({
                          title: `Rollback ${d.task}`,
                          message: `Roll back from ${d.version}?`,
                          label: '↩️ Rollback',
                          type: 'rollback',
                          action: () => handleRollback(d.id),
                        })}>
                        ↩ Rollback
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ══ TAB: Audit Log ══ */}
      {tab === 'Audit Log' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="dep__tbl-hd">
            <h3 className="dep__tbl-title">Deployment Audit Log</h3>
            <button className="btn btn--ghost btn--sm" onClick={loadAll}>↻ Refresh</button>
          </div>
          {log.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No deployment actions yet
            </div>
          ) : (
            <table className="tbl">
              <thead>
                <tr><th>TIMESTAMP</th><th>ACTION</th><th>MODEL</th><th>DETAIL</th><th>BY</th></tr>
              </thead>
              <tbody>
                {log.map((entry, i) => (
                  <tr key={i}>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{entry.timestamp}</td>
                    <td>
                      <span className={`badge badge--${
                        entry.action === 'deploy'   ? 'green'  :
                        entry.action === 'rollback' ? 'yellow' :
                        entry.action === 'stop'     ? 'red'    : 'gray'
                      }`}>
                        {entry.action}
                      </span>
                    </td>
                    <td>{MODEL_ICON[entry.model]} {entry.model}</td>
                    <td style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{entry.detail}</td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{entry.actor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
