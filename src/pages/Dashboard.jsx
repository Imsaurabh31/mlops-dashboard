import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

const STATS = [
  { label: 'Total Images',  value: '12,480', delta: '+248 today',  deltaUp: true,  icon: '🖼',  color: 'blue'   },
  { label: 'Curated',       value: '9,312',  delta: '74.6% done',  deltaUp: true,  icon: '✅',  color: 'green'  },
  { label: 'Pending',       value: '3,168',  delta: '25.4% left',  deltaUp: false, icon: '⏳',  color: 'yellow' },
  { label: 'Active Users',  value: '8',      delta: '2 online now', deltaUp: true, icon: '👥',  color: 'purple' },
];

const QUICK_ACTIONS = [
  { icon: '✏️', label: 'Curation',       desc: 'Annotate VLM inference results',           to: '/curation', badge: '3,168 pending' },
  { icon: '⚙️', label: 'Admin Panel',    desc: 'Manage users and batch assignments',        to: '/admin',    badge: '6 batches'    },
  { icon: '🧠', label: 'Model Training', desc: 'Train classification models from data',     to: '/training', badge: '1 running'    },
];

const ACTIVITY = [
  { user: 'alice@oly.com',  action: 'Curated 42 images',   ref: 'Batch-007',  time: '2 min ago',  status: 'completed' },
  { user: 'bob@oly.com',    action: 'Training job started', ref: 'gender-v3',  time: '15 min ago', status: 'running'   },
  { user: 'carol@oly.com',  action: 'Curated 18 images',   ref: 'Batch-008',  time: '34 min ago', status: 'completed' },
  { user: 'dave@oly.com',   action: 'Batch assigned',       ref: 'Batch-009',  time: '1 hr ago',   status: 'pending'   },
  { user: 'eve@oly.com',    action: 'Model deployed',       ref: 'age-v2',     time: '2 hr ago',   status: 'deployed'  },
];

const STATUS_BADGE = {
  completed: 'green',
  running:   'blue',
  pending:   'yellow',
  deployed:  'purple',
  failed:    'red',
};

const PIPELINE = [
  { label: 'Annotation Progress',           pct: 74,  color: '#2563eb' },
  { label: 'Gender Model Accuracy',         pct: 92,  color: '#16a34a' },
  { label: 'Age Model Accuracy',            pct: 87,  color: '#7c3aed' },
  { label: 'Staff Detection Accuracy',      pct: 95,  color: '#0891b2' },
];

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dash">

      {/* ── Stats row ── */}
      <div className="dash__stats">
        {STATS.map((s) => (
          <div key={s.label} className={`dash-stat card dash-stat--${s.color}`}>
            <div className="dash-stat__top">
              <span className="dash-stat__icon">{s.icon}</span>
              <span className={`dash-stat__delta${s.deltaUp ? ' dash-stat__delta--up' : ' dash-stat__delta--down'}`}>
                {s.deltaUp ? '↑' : '↓'} {s.delta}
              </span>
            </div>
            <div className="dash-stat__value">{s.value}</div>
            <div className="dash-stat__label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="dash__cols">

        {/* ── Left column ── */}
        <div className="dash__col-main">

          {/* Quick actions */}
          <section className="dash__section">
            <div className="dash__section-hd">
              <h2 className="dash__section-title">Quick Actions</h2>
            </div>
            <div className="dash__actions">
              {QUICK_ACTIONS.map((a) => (
                <button
                  key={a.label}
                  className="action-card card"
                  onClick={() => navigate(a.to)}
                >
                  <div className="action-card__head">
                    <span className="action-card__icon">{a.icon}</span>
                    <span className="badge badge--blue">{a.badge}</span>
                  </div>
                  <div className="action-card__title">{a.label}</div>
                  <div className="action-card__desc">{a.desc}</div>
                  <div className="action-card__cta">Open →</div>
                </button>
              ))}
            </div>
          </section>

          {/* Recent activity */}
          <section className="dash__section">
            <div className="dash__section-hd">
              <h2 className="dash__section-title">Recent Activity</h2>
              {/* Refresh note: will fetch live data once API is connected */}
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => alert('Live activity feed will be available once the backend API is connected.')}
                title="Coming soon — requires backend API"
              >
                ↻ Refresh
              </button>
            </div>
            <div className="card" style={{ overflow: 'hidden' }}>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>USER</th>
                    <th>ACTION</th>
                    <th>REF</th>
                    <th>TIME</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {ACTIVITY.map((row, i) => (
                    <tr key={i}>
                      <td>
                        <div className="dash__user-cell">
                          <div className="dash__user-avatar">{row.user[0].toUpperCase()}</div>
                          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{row.user}</span>
                        </div>
                      </td>
                      <td>{row.action}</td>
                      <td><span className="chip">📦 {row.ref}</span></td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{row.time}</td>
                      <td><span className={`badge badge--${STATUS_BADGE[row.status]}`}>{row.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* ── Right column ── */}
        <div className="dash__col-side">

          {/* Pipeline health */}
          <section className="dash__section">
            <div className="dash__section-hd">
              <h2 className="dash__section-title">Pipeline Health</h2>
            </div>
            <div className="card dash__pipeline">
              {PIPELINE.map((p) => (
                <div key={p.label} className="dash__pipeline-row">
                  <div className="dash__pipeline-info">
                    <span className="dash__pipeline-label">{p.label}</span>
                    <span className="dash__pipeline-pct" style={{ color: p.color }}>{p.pct}%</span>
                  </div>
                  <div className="progress-bar-wrap">
                    <div className="progress-bar" style={{ width: `${p.pct}%`, background: p.color }} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* System status */}
          <section className="dash__section">
            <div className="dash__section-hd">
              <h2 className="dash__section-title">System Status</h2>
            </div>
            <div className="card dash__status-list">
              {[
                { name: 'Annotation API',    ok: true  },
                { name: 'Training Server',   ok: true  },
                { name: 'Model Inference',   ok: true  },
                { name: 'Storage Bucket',    ok: false },
              ].map((s) => (
                <div key={s.name} className="dash__status-row">
                  <span className={`dash__status-dot ${s.ok ? 'dash__status-dot--green' : 'dash__status-dot--red'}`} />
                  <span className="dash__status-name">{s.name}</span>
                  <span className={`badge ${s.ok ? 'badge--green' : 'badge--red'}`} style={{ marginLeft: 'auto' }}>
                    {s.ok ? 'Operational' : 'Degraded'}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Storage */}
          <section className="dash__section">
            <div className="dash__section-hd">
              <h2 className="dash__section-title">Storage</h2>
            </div>
            <div className="card dash__storage">
              <div className="dash__storage-ring">
                <svg viewBox="0 0 36 36" className="dash__ring-svg">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--border)" strokeWidth="3.2"/>
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--accent-blue)"
                    strokeWidth="3.2" strokeDasharray="74.6 25.4"
                    strokeDashoffset="25" strokeLinecap="round"/>
                </svg>
                <div className="dash__ring-label">
                  <span className="dash__ring-pct">74%</span>
                  <span className="dash__ring-sub">used</span>
                </div>
              </div>
              <div className="dash__storage-info">
                <div className="dash__storage-row">
                  <span className="dash__storage-dot" style={{ background: 'var(--accent-blue)' }} />
                  <span>Images</span>
                  <span className="dash__storage-val">186 GB</span>
                </div>
                <div className="dash__storage-row">
                  <span className="dash__storage-dot" style={{ background: 'var(--accent-purple)' }} />
                  <span>Models</span>
                  <span className="dash__storage-val">42 GB</span>
                </div>
                <div className="dash__storage-row">
                  <span className="dash__storage-dot" style={{ background: 'var(--border-strong)' }} />
                  <span>Free</span>
                  <span className="dash__storage-val">80 GB</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
