import { useState } from 'react';
import './Training.css';

const MODEL_CARDS = [
  {
    id: 'gender', title: 'Gender Classification',
    images: 9312, classes: 2, accuracy: 92,
    tags: ['Male', 'Female'],
    color: 'blue', btnLabel: 'Train Gender Model',
  },
  {
    id: 'age', title: 'Age Classification',
    images: 9312, classes: 5, accuracy: 87,
    tags: ['Infant', 'Child', 'Teen', 'Adult', 'Mature'],
    color: 'purple', btnLabel: 'Train Age Model',
  },
  {
    id: 'staff', title: 'Staff Detection',
    images: 9312, classes: 2, accuracy: 95,
    tags: ['Staff', 'Customer'],
    color: 'teal', btnLabel: 'Train Staff Model',
  },
];

const JOBS = [
  { id: 'JOB-1024', task: 'Gender Classification', status: 'completed', started: '2026-10-28 09:14', duration: '4m 32s', accuracy: '92.4%' },
  { id: 'JOB-1023', task: 'Age Classification',    status: 'running',   started: '2026-10-28 10:55', duration: '—',       accuracy: '—'     },
  { id: 'JOB-1022', task: 'Staff Detection',        status: 'completed', started: '2026-10-27 18:02', duration: '6m 11s',  accuracy: '95.1%' },
  { id: 'JOB-1021', task: 'Gender Classification',  status: 'failed',    started: '2026-10-27 14:30', duration: '1m 03s',  accuracy: '—'     },
  { id: 'JOB-1020', task: 'Age Classification',     status: 'completed', started: '2026-10-26 11:00', duration: '5m 48s',  accuracy: '86.9%' },
];

const EXPERIMENTS = [
  { name: 'gender-v3', model: 'ResNet-50',        dataset: '9.3k', val_acc: '92.4%', date: '2026-10-28', status: 'best'     },
  { name: 'gender-v2', model: 'MobileNet-V2',     dataset: '7.1k', val_acc: '89.1%', date: '2026-10-25', status: 'archived' },
  { name: 'age-v2',    model: 'EfficientNet-B0',  dataset: '9.3k', val_acc: '87.3%', date: '2026-10-27', status: 'best'     },
  { name: 'staff-v2',  model: 'ResNet-34',        dataset: '9.3k', val_acc: '95.1%', date: '2026-10-27', status: 'deployed' },
];

const DEPLOYED = [
  { name: 'gender-v3', endpoint: '/api/infer/gender', latency: '18ms', req: '1.2k/hr', uptime: '99.8%' },
  { name: 'staff-v2',  endpoint: '/api/infer/staff',  latency: '22ms', req: '1.2k/hr', uptime: '99.9%' },
  { name: 'age-v2',    endpoint: '/api/infer/age',    latency: '25ms', req: '1.2k/hr', uptime: '99.5%' },
];

const JOB_BADGE = { completed: 'green', running: 'blue', failed: 'red', pending: 'yellow' };
const EXP_BADGE = { best: 'green', archived: 'gray', deployed: 'purple' };
const CARD_COLOR = { blue: 'var(--accent-blue)', purple: 'var(--accent-purple)', teal: 'var(--accent-teal)' };
const CARD_LIGHT = { blue: 'var(--accent-blue-light)', purple: 'var(--accent-purple-light)', teal: 'var(--accent-teal-light)' };

const TABS = ['Training Jobs', 'Experiments', 'Deployed Models'];

export default function Training() {
  const [tab, setTab] = useState('Training Jobs');
  const [states, setStates] = useState({});

  const train = (id) => {
    setStates((p) => ({ ...p, [id]: 'training' }));
    setTimeout(() => setStates((p) => ({ ...p, [id]: 'done' })), 3000);
  };

  return (
    <div className="trn">

      {/* ── Model cards ── */}
      <div className="trn__cards">
        {MODEL_CARDS.map((m) => {
          const st = states[m.id];
          return (
            <div className="trn-card card" key={m.id} style={{ '--mc': CARD_COLOR[m.color], '--ml': CARD_LIGHT[m.color] }}>
              <div className="trn-card__hd">
                <h3 className="trn-card__title">{m.title}</h3>
                <span className={`badge badge--${st === 'training' ? 'blue' : st === 'done' ? 'green' : 'yellow'}`}>
                  {st === 'training' ? 'Training…' : st === 'done' ? 'Trained ✓' : 'Ready'}
                </span>
              </div>

              <div className="trn-card__stats">
                <div className="trn-card__stat">
                  <span className="trn-card__stat-val" style={{ color: 'var(--mc)' }}>{m.images.toLocaleString()}</span>
                  <span className="trn-card__stat-label">Images</span>
                </div>
                <div className="trn-card__divider" />
                <div className="trn-card__stat">
                  <span className="trn-card__stat-val" style={{ color: 'var(--mc)' }}>{m.classes}</span>
                  <span className="trn-card__stat-label">Classes</span>
                </div>
                <div className="trn-card__divider" />
                <div className="trn-card__stat">
                  <span className="trn-card__stat-val" style={{ color: 'var(--mc)' }}>{m.accuracy}%</span>
                  <span className="trn-card__stat-label">Last Acc.</span>
                </div>
              </div>

              <div className="trn-card__tags">
                {m.tags.map((t) => (
                  <span key={t} className="chip" style={{ borderColor: 'var(--mc)', color: 'var(--mc)', background: 'var(--ml)' }}>{t}</span>
                ))}
              </div>

              {st === 'training' ? (
                <div className="trn-card__progress progress-bar-wrap">
                  <div className="trn-card__progress-anim" style={{ background: 'var(--mc)' }} />
                </div>
              ) : (
                <button
                  className="trn-card__btn btn"
                  style={{ background: 'var(--mc)', color: '#fff', border: 'none', justifyContent: 'center', width: '100%' }}
                  onClick={() => train(m.id)}
                  disabled={st === 'done'}
                >
                  {st === 'done' ? '✓ Trained' : m.btnLabel}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Tabs ── */}
      <div className="trn__tabs">
        {TABS.map((t) => (
          <button key={t} className={`trn__tab${tab === t ? ' trn__tab--active' : ''}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {/* ── Tab body ── */}
      {tab === 'Training Jobs' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="trn__tbl-hd">
            <h3 className="trn__tbl-title">Active &amp; Recent Jobs</h3>
            <button className="btn btn--ghost btn--sm">↻ Refresh</button>
          </div>
          <table className="tbl">
            <thead><tr>
              <th>JOB ID</th><th>TASK</th><th>STATUS</th><th>STARTED</th><th>DURATION</th><th>ACCURACY</th><th>ACTIONS</th>
            </tr></thead>
            <tbody>
              {JOBS.map((j) => (
                <tr key={j.id}>
                  <td><code className="trn__code">{j.id}</code></td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{j.task}</td>
                  <td>
                    <span className={`badge badge--${JOB_BADGE[j.status]}`}>
                      {j.status === 'running' && <span className="trn__pulse" />}
                      {j.status.charAt(0).toUpperCase() + j.status.slice(1)}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{j.started}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{j.duration}</td>
                  <td style={{ fontWeight: 700, color: j.accuracy !== '—' ? 'var(--accent-green)' : 'var(--text-muted)' }}>{j.accuracy}</td>
                  <td><button className="btn btn--ghost btn--sm">View Logs</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'Experiments' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="trn__tbl-hd">
            <h3 className="trn__tbl-title">Experiment Tracker</h3>
          </div>
          <table className="tbl">
            <thead><tr>
              <th>EXPERIMENT</th><th>MODEL</th><th>DATASET</th><th>VAL ACCURACY</th><th>DATE</th><th>STATUS</th>
            </tr></thead>
            <tbody>
              {EXPERIMENTS.map((e) => (
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

      {tab === 'Deployed Models' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="trn__tbl-hd">
            <h3 className="trn__tbl-title">Live Deployments</h3>
          </div>
          <table className="tbl">
            <thead><tr>
              <th>MODEL</th><th>ENDPOINT</th><th>LATENCY</th><th>REQUESTS</th><th>UPTIME</th><th>ACTIONS</th>
            </tr></thead>
            <tbody>
              {DEPLOYED.map((d) => (
                <tr key={d.name}>
                  <td><code className="trn__code">{d.name}</code></td>
                  <td><span className="chip">🔗 {d.endpoint}</span></td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{d.latency}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{d.req}</td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-green)' }}>{d.uptime}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn--ghost btn--sm">Manage</button>
                      <button className="btn btn--danger btn--sm">Stop</button>
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
