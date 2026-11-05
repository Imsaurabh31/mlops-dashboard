import { useState, useMemo } from 'react';
import './Admin.css';

/* ── Seed data ── */
const SEED_BATCHES = [
  { id: 1, name: 'Batch-001', client: 'RetailCo',  assigned: 'alice@oly.com',  images: 500, pct: 100, status: 'completed'   },
  { id: 2, name: 'Batch-002', client: 'ShopMart',  assigned: 'bob@oly.com',    images: 480, pct: 72,  status: 'in-progress' },
  { id: 3, name: 'Batch-003', client: 'FreshMart', assigned: 'carol@oly.com',  images: 320, pct: 45,  status: 'in-progress' },
  { id: 4, name: 'Batch-004', client: 'RetailCo',  assigned: 'dave@oly.com',   images: 600, pct: 10,  status: 'in-progress' },
  { id: 5, name: 'Batch-005', client: 'MegaStore', assigned: null,             images: 400, pct: 0,   status: 'unassigned'  },
  { id: 6, name: 'Batch-006', client: 'FreshMart', assigned: 'eve@oly.com',    images: 550, pct: 88,  status: 'in-progress' },
];

const USERS = [
  { name: 'Alice Chen',   email: 'alice@oly.com',  role: 'Curator', batches: 2, curated: 500, active: true  },
  { name: 'Bob Smith',    email: 'bob@oly.com',    role: 'Curator', batches: 1, curated: 346, active: true  },
  { name: 'Carol Davis',  email: 'carol@oly.com',  role: 'Curator', batches: 1, curated: 144, active: true  },
  { name: 'Dave Wilson',  email: 'dave@oly.com',   role: 'Curator', batches: 1, curated: 60,  active: false },
  { name: 'Eve Martinez', email: 'eve@oly.com',    role: 'Curator', batches: 1, curated: 484, active: true  },
  { name: 'Admin User',   email: 'admin@oly.com',  role: 'Admin',   batches: 0, curated: 0,   active: true  },
];

const BATCH_BADGE = { completed: 'green', 'in-progress': 'blue', unassigned: 'yellow' };
const BATCH_BAR   = {
  completed:    'var(--accent-green)',
  'in-progress':'var(--accent-blue)',
  unassigned:   'var(--accent-yellow)',
};

const EMPTY_FORM = { name: '', client: '', assignee: '', images: '' };
const TABS = ['Batch Assignments', 'User Management', 'Progress Overview'];

/* find display name for an email */
const nameFor = (email) => USERS.find((u) => u.email === email)?.name ?? email;

export default function Admin() {
  const [tab, setTab]         = useState('Batch Assignments');
  const [batches, setBatches] = useState(SEED_BATCHES);
  const [nextId, setNextId]   = useState(7);

  /* ── Create modal ── */
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm]             = useState(EMPTY_FORM);
  const [errors, setErrors]         = useState({});
  const [shakeCreate, setShakeCreate] = useState(false);
  const [toast, setToast]           = useState(null);

  /* ── Edit modal ── */
  const [editBatch, setEditBatch]   = useState(null);
  const [editForm, setEditForm]     = useState(EMPTY_FORM);
  const [editErrors, setEditErrors] = useState({});
  const [shakeEdit, setShakeEdit]   = useState(false);

  /* ── Delete confirm ── */
  const [deletingId, setDeletingId] = useState(null);

  /* ── Derived stats ── */
  const stats = useMemo(() => {
    const totalImages  = batches.reduce((s, b) => s + b.images, 0);
    const assigned     = batches.filter((b) => b.assigned).reduce((s, b) => s + b.images, 0);
    const curated      = batches.reduce((s, b) => s + Math.round(b.images * b.pct / 100), 0);
    const unassigned   = batches.filter((b) => !b.assigned).reduce((s, b) => s + b.images, 0);
    return [
      { label: 'Total Images', value: totalImages.toLocaleString(), icon: '🖼', color: 'blue'   },
      { label: 'Assigned',     value: assigned.toLocaleString(),    icon: '📋', color: 'purple' },
      { label: 'Curated',      value: curated.toLocaleString(),     icon: '✅', color: 'green'  },
      { label: 'Unassigned',   value: unassigned.toLocaleString(),  icon: '⏳', color: 'yellow' },
      { label: 'Active Users', value: USERS.filter((u) => u.active).length.toString(), icon: '👥', color: 'teal' },
    ];
  }, [batches]);

  /* ── Helpers ── */
  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const validate = (f) => {
    const e = {};
    if (!f.name.trim())             e.name   = 'Batch name is required';
    else if (batches.some((b) => b.name.toLowerCase() === f.name.trim().toLowerCase() && b.id !== editBatch?.id))
                                    e.name   = 'Batch name already exists';
    if (!f.client.trim())           e.client = 'Client is required';
    if (!f.images || !Number.isInteger(Number(f.images)) || Number(f.images) < 1)
                                    e.images = 'Enter a valid whole number';
    return e;
  };

  /* ── Create ── */
  const openCreate = () => { setForm(EMPTY_FORM); setErrors({}); setShowCreate(true); };

  const submitCreate = (e) => {
    e.preventDefault();
    const errs = validate(form);
    if (Object.keys(errs).length) {
      setErrors(errs);
      setShakeCreate(true);
      setTimeout(() => setShakeCreate(false), 400);
      return;
    }

    const newBatch = {
      id:       nextId,
      name:     form.name.trim(),
      client:   form.client.trim(),
      assigned: form.assignee || null,
      images:   Math.floor(Number(form.images)), // integer only
      pct:      0,
      status:   form.assignee ? 'in-progress' : 'unassigned',
      _isNew:   true, // flag for highlight — cleared after animation
    };
    setBatches((prev) => [newBatch, ...prev]);
    setNextId((n) => n + 1);
    // Clear the _isNew flag after animation completes
    setTimeout(() => {
      setBatches((prev) => prev.map(b => b.id === newBatch.id ? { ...b, _isNew: false } : b));
    }, 2000);
    setShowCreate(false);
    setForm(EMPTY_FORM);
    setErrors({});
    showToast(`✅ "${newBatch.name}" created successfully`);
  };

  /* ── Edit ── */
  const openEdit = (batch) => {
    setEditBatch(batch);
    setEditForm({ name: batch.name, client: batch.client, assignee: batch.assigned ?? '', images: String(batch.images) });
    setEditErrors({});
  };

  const submitEdit = (e) => {
    e.preventDefault();
    const errs = validate(editForm);
    if (Object.keys(errs).length) {
      setEditErrors(errs);
      setShakeEdit(true);
      setTimeout(() => setShakeEdit(false), 400);
      return;
    }

    setBatches((prev) => prev.map((b) =>
      b.id === editBatch.id
        ? {
            ...b,
            name:     editForm.name.trim(),
            client:   editForm.client.trim(),
            assigned: editForm.assignee || null,
            images:   Number(editForm.images),
            status:   editForm.assignee ? (b.pct === 100 ? 'completed' : 'in-progress') : 'unassigned',
          }
        : b
    ));
    showToast(`✏️ "${editForm.name}" updated`);
    setEditBatch(null);
  };

  /* ── Delete ── */
  const confirmDelete = (id) => setDeletingId(id);

  const doDelete = () => {
    const name = batches.find((b) => b.id === deletingId)?.name;
    setBatches((prev) => prev.filter((b) => b.id !== deletingId));
    setDeletingId(null);
    showToast(`🗑 "${name}" deleted`, 'danger');
  };

  /* ── Field helpers ── */
  const field = (label, key, type, ph, f, setF, errs, setErrs) => (
    <div className="adm-field" key={key}>
      <label className="adm-field__label">{label}</label>
      <input
        className={`adm-field__input${errs[key] ? ' adm-field__input--error' : ''}`}
        type={type} placeholder={ph}
        value={f[key]}
        onChange={(e) => {
          setF((prev) => ({ ...prev, [key]: e.target.value }));
          if (errs[key]) setErrs((p) => ({ ...p, [key]: '' }));
        }}
        required
      />
      {errs[key] && <span className="adm-field__error">{errs[key]}</span>}
    </div>
  );

  const assigneeSelect = (f, setF) => (
    <div className="adm-field">
      <label className="adm-field__label">Assign To <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
      <select className="adm-field__input" value={f.assignee} onChange={(e) => setF((prev) => ({ ...prev, assignee: e.target.value }))}>
        <option value="">— Unassigned —</option>
        {USERS.filter((u) => u.role === 'Curator').map((u) => (
          <option key={u.email} value={u.email}>{u.name} ({u.email})</option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="adm">

      {/* ── Toast ── */}
      {toast && (
        <div className={`adm-toast adm-toast--${toast.type}`}>
          {toast.msg}
        </div>
      )}

      {/* ── Stats ── */}
      <div className="adm__stats">
        {stats.map((s) => (
          <div key={s.label} className={`adm-stat card adm-stat--${s.color}`}>
            <div className="adm-stat__icon">{s.icon}</div>
            <div className="adm-stat__val">{s.value}</div>
            <div className="adm-stat__label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Tabs ── */}
      <div className="adm__tabs">
        {TABS.map((t) => (
          <button key={t} className={`adm__tab${tab === t ? ' adm__tab--active' : ''}`} onClick={() => setTab(t)}>
            {t === 'Batch Assignments'  && '🗂 '}
            {t === 'User Management'    && '👥 '}
            {t === 'Progress Overview'  && '📊 '}
            {t}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════════
          TAB: Batch Assignments
      ══════════════════════════════════ */}
      {tab === 'Batch Assignments' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="adm__tbl-hd">
            <div>
              <h3 className="adm__tbl-title">Batch Assignments</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                {batches.length} total · {batches.filter((b) => b.status === 'completed').length} completed
              </p>
            </div>
            <button className="btn btn--primary btn--sm" onClick={openCreate}>+ Create Batch</button>
          </div>
          <table className="tbl">
            <thead>
              <tr>
                <th>BATCH</th><th>CLIENT</th><th>ASSIGNED TO</th>
                <th>IMAGES</th><th>PROGRESS</th><th>STATUS</th><th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id} className={b._isNew ? 'adm__row--new' : ''}>
                  <td><span className="chip">📦 {b.name}</span></td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{b.client}</td>
                  <td>
                    {b.assigned
                      ? <div className="adm__user-cell">
                          <div className="adm__avatar">{b.assigned[0].toUpperCase()}</div>
                          <div>
                            <div style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 13 }}>
                              {nameFor(b.assigned)}
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{b.assigned}</div>
                          </div>
                        </div>
                      : <span className="badge badge--yellow">⚠ Unassigned</span>
                    }
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{b.images.toLocaleString()}</td>
                  <td>
                    <div className="adm__prog-cell">
                      <div className="progress-bar-wrap" style={{ flex: 1 }}>
                        <div className="progress-bar" style={{ width: `${b.pct}%`, background: BATCH_BAR[b.status] }} />
                      </div>
                      <span className="adm__prog-pct">{b.pct}%</span>
                    </div>
                  </td>
                  <td><span className={`badge badge--${BATCH_BADGE[b.status]}`}>{b.status}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: 5 }}>
                      <button className="btn btn--ghost btn--sm" onClick={() => openEdit(b)}>Edit</button>
                      <button className="btn btn--danger btn--sm" onClick={() => confirmDelete(b.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
              {batches.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
                    No batches yet. Create one to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ══════════════════════════════════
          TAB: User Management
      ══════════════════════════════════ */}
      {tab === 'User Management' && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div className="adm__tbl-hd">
            <h3 className="adm__tbl-title">User Management</h3>
            <button className="btn btn--primary btn--sm">+ Add User</button>
          </div>
          <table className="tbl">
            <thead>
              <tr><th>NAME</th><th>EMAIL</th><th>ROLE</th><th>BATCHES</th><th>CURATED</th><th>STATUS</th><th>ACTIONS</th></tr>
            </thead>
            <tbody>
              {USERS.map((u) => (
                <tr key={u.email}>
                  <td>
                    <div className="adm__user-cell">
                      <div className="adm__avatar">{u.name[0]}</div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{u.name}</span>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{u.email}</td>
                  <td><span className={`badge badge--${u.role === 'Admin' ? 'purple' : 'blue'}`}>{u.role}</span></td>
                  <td style={{ color: 'var(--text-muted)' }}>{u.batches}</td>
                  <td style={{ fontWeight: 700, color: 'var(--accent-blue)' }}>{u.curated.toLocaleString()}</td>
                  <td>
                    <span className={`badge badge--${u.active ? 'green' : 'gray'}`}>
                      {u.active ? '● Active' : '○ Inactive'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 5 }}>
                      <button className="btn btn--ghost btn--sm">Edit</button>
                      <button className="btn btn--ghost btn--sm">Assign</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ══════════════════════════════════
          TAB: Progress Overview
      ══════════════════════════════════ */}
      {tab === 'Progress Overview' && (
        <div className="adm__progress-view">
          <div className="card" style={{ overflow: 'hidden', marginBottom: 16 }}>
            <div className="adm__tbl-hd">
              <h3 className="adm__tbl-title">Curator Performance</h3>
            </div>
            <div className="adm__perf-list">
              {USERS.filter((u) => u.role === 'Curator').map((u) => {
                const pct = Math.round((u.curated / 600) * 100);
                return (
                  <div key={u.email} className="adm__perf-row">
                    <div className="adm__user-cell" style={{ minWidth: 180 }}>
                      <div className="adm__avatar">{u.name[0]}</div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{u.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.curated.toLocaleString()} images</div>
                      </div>
                    </div>
                    <div className="progress-bar-wrap" style={{ flex: 1 }}>
                      <div className="progress-bar" style={{
                        width: `${pct}%`,
                        background: u.active ? 'var(--accent-blue)' : 'var(--border-strong)',
                      }} />
                    </div>
                    <span className="adm__perf-pct">{pct}%</span>
                    <span className={`badge badge--${u.active ? 'green' : 'gray'}`}>{u.active ? 'Active' : 'Inactive'}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="adm__summary">
            {[
              { label: 'Avg. per Curator',  value: '306',        sub: 'images curated',  color: 'var(--accent-blue)'   },
              { label: 'Top Curator',        value: 'Alice Chen', sub: '500 images',      color: 'var(--accent-purple)' },
              { label: 'Overall Progress',   value: '74.6%',      sub: '9,312 / 12,480', color: 'var(--accent-green)'  },
              { label: 'Est. Completion',    value: '2 days',     sub: 'at current rate', color: 'var(--accent-yellow)' },
            ].map((s) => (
              <div key={s.label} className="adm-summary-card card">
                <span className="adm-summary-card__label">{s.label}</span>
                <span className="adm-summary-card__val" style={{ color: s.color }}>{s.value}</span>
                <span className="adm-summary-card__sub">{s.sub}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════
          MODAL: Create Batch
      ══════════════════════════════════ */}
      {showCreate && (
        <div className="adm-modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="adm-modal card" onClick={(e) => e.stopPropagation()}>
            <div className="adm-modal__hd">
              <div>
                <h3 className="adm-modal__title">Create New Batch</h3>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  Fill in the details below to create a new annotation batch.
                </p>
              </div>
              <button className="adm-modal__close" onClick={() => setShowCreate(false)}>✕</button>
            </div>
            <form className={`adm-modal__form${shakeCreate ? ' adm-modal__form--shake' : ''}`} onSubmit={submitCreate} noValidate>
              {field('Batch Name',       'name',   'text',   'e.g. Batch-007', form, setForm, errors, setErrors)}
              {field('Client',           'client', 'text',   'e.g. RetailCo',  form, setForm, errors, setErrors)}
              {field('Number of Images', 'images', 'number', 'e.g. 500',       form, setForm, errors, setErrors)}
              {assigneeSelect(form, setForm)}
              <div className="adm-modal__actions">
                <button type="button" className="btn btn--ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn--primary">Create Batch</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════
          MODAL: Edit Batch
      ══════════════════════════════════ */}
      {editBatch && (
        <div className="adm-modal-overlay" onClick={() => setEditBatch(null)}>
          <div className="adm-modal card" onClick={(e) => e.stopPropagation()}>
            <div className="adm-modal__hd">
              <div>
                <h3 className="adm-modal__title">Edit Batch</h3>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  Editing <strong>{editBatch.name}</strong>
                </p>
              </div>
              <button className="adm-modal__close" onClick={() => setEditBatch(null)}>✕</button>
            </div>
            <form className={`adm-modal__form${shakeEdit ? ' adm-modal__form--shake' : ''}`} onSubmit={submitEdit} noValidate>
              {field('Batch Name',       'name',   'text',   'e.g. Batch-007', editForm, setEditForm, editErrors, setEditErrors)}
              {field('Client',           'client', 'text',   'e.g. RetailCo',  editForm, setEditForm, editErrors, setEditErrors)}
              {field('Number of Images', 'images', 'number', 'e.g. 500',       editForm, setEditForm, editErrors, setEditErrors)}
              {assigneeSelect(editForm, setEditForm)}
              <div className="adm-modal__actions">
                <button type="button" className="btn btn--ghost" onClick={() => setEditBatch(null)}>Cancel</button>
                <button type="submit" className="btn btn--primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════
          MODAL: Delete Confirm
      ══════════════════════════════════ */}
      {deletingId && (
        <div className="adm-modal-overlay" onClick={() => setDeletingId(null)}>
          <div className="adm-modal adm-modal--sm card" onClick={(e) => e.stopPropagation()}>
            <div className="adm-modal__hd">
              <h3 className="adm-modal__title">Delete Batch</h3>
              <button className="adm-modal__close" onClick={() => setDeletingId(null)}>✕</button>
            </div>
            <div className="adm-delete-body">
              <div className="adm-delete-icon">🗑</div>
              <p className="adm-delete-text">
                Are you sure you want to delete <strong>{batches.find((b) => b.id === deletingId)?.name}</strong>?
              </p>
              <p className="adm-delete-sub">This action cannot be undone.</p>
            </div>
            <div className="adm-modal__actions">
              <button className="btn btn--ghost" onClick={() => setDeletingId(null)}>Cancel</button>
              <button className="btn" style={{ background: 'var(--accent-red)', color: '#fff', border: 'none' }} onClick={doDelete}>
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
