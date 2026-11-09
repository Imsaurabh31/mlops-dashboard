import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './Curation.css';

/* ── Palettes ── */
const PALETTES = [
  { bg: '#dbeafe', fg: '#1e40af', dark_bg: '#1e3a5f', dark_fg: '#93c5fd' },
  { bg: '#dcfce7', fg: '#166534', dark_bg: '#14532d', dark_fg: '#86efac' },
  { bg: '#fef3c7', fg: '#92400e', dark_bg: '#451a03', dark_fg: '#fcd34d' },
  { bg: '#ede9fe', fg: '#5b21b6', dark_bg: '#2e1065', dark_fg: '#c4b5fd' },
  { bg: '#fee2e2', fg: '#991b1b', dark_bg: '#450a0a', dark_fg: '#fca5a5' },
  { bg: '#e0f2fe', fg: '#075985', dark_bg: '#0c4a6e', dark_fg: '#7dd3fc' },
  { bg: '#fce7f3', fg: '#9d174d', dark_bg: '#500724', dark_fg: '#f9a8d4' },
  { bg: '#f0fdf4', fg: '#14532d', dark_bg: '#052e16', dark_fg: '#6ee7b7' },
  { bg: '#fff7ed', fg: '#7c2d12', dark_bg: '#431407', dark_fg: '#fdba74' },
  { bg: '#f5f3ff', fg: '#4c1d95', dark_bg: '#2e1065', dark_fg: '#a78bfa' },
];

const LOCATIONS = ['Store Entrance', 'Aisle 3', 'Checkout', 'Parking Lot', 'Lobby'];
const GENDERS   = ['Male', 'Female'];

const PRESET_ANN = [
  { gender: 'M', age: '4', staff: 'S', id: 'Y' },
  { gender: 'F', age: '5', staff: 'N', id: 'N' },
  { gender: 'M', age: '3', staff: 'N', id: 'N' },
  { gender: 'F', age: '4', staff: 'S', id: 'Y' },
  { gender: 'M', age: '5', staff: 'N', id: 'N' },
];

const MOCK_IMAGES = Array.from({ length: 24 }, (_, i) => ({
  id: i + 1,
  label: `IMG_${String(i + 1).padStart(4, '0')}`,
  curated: i < 5,
  annotations: i < 5 ? PRESET_ANN[i] : null,
  palette: PALETTES[i % PALETTES.length],
  shape: i % 3,
  location: LOCATIONS[i % LOCATIONS.length],
  gender: GENDERS[i % 2],
  timestamp: `2026-10-${String(28 - (i % 3)).padStart(2, '0')} ${String(10 + (i % 12)).padStart(2, '0')}:${String(i * 3 % 60).padStart(2, '0')}`,
}));

const ANNOTATION_GROUPS = [
  {
    field: 'gender', title: 'Gender Classification', icon: '👤',
    options: [
      { key: 'M', label: 'male',   shortcut: 'M', color: '#6366f1' },
      { key: 'F', label: 'female', shortcut: 'F', color: '#ec4899' },
      { key: 'R', label: 'reject', shortcut: 'X', color: '#ef4444', isReject: true },
    ],
  },
  {
    field: 'age', title: 'Age Classification', icon: '📅',
    options: [
      { key: '1', label: 'infant',  shortcut: '1', color: '#06b6d4' },
      { key: '2', label: 'child',   shortcut: '2', color: '#3b82f6' },
      { key: '3', label: 'teen',    shortcut: '3', color: '#8b5cf6' },
      { key: '4', label: 'adult',   shortcut: '4', color: '#10b981' },
      { key: '5', label: 'mature',  shortcut: '5', color: '#f59e0b' },
      { key: 'R', label: 'reject',  shortcut: 'R', color: '#ef4444', isReject: true },
    ],
  },
  {
    field: 'staff', title: 'Staff Classification', icon: '👔',
    options: [
      { key: 'S', label: 'staff',     shortcut: 'S', color: '#10b981' },
      { key: 'N', label: 'non_staff', shortcut: 'N', color: '#6366f1' },
      { key: 'R', label: 'reject',    shortcut: 'Z', color: '#ef4444', isReject: true },
    ],
  },
  {
    field: 'id', title: 'ID Card Visibility', icon: '🪪',
    options: [
      { key: 'Y', label: 'visible',     shortcut: 'V', color: '#10b981' },
      { key: 'N', label: 'not_visible', shortcut: 'H', color: '#6366f1' },
      { key: 'R', label: 'reject',      shortcut: 'B', color: '#ef4444', isReject: true },
    ],
  },
];

const ANN_LABELS = {
  gender: { M: 'Male', F: 'Female', R: 'Rejected' },
  age:    { '1': 'Infant', '2': 'Child', '3': 'Teen', '4': 'Adult', '5': 'Mature', R: 'Rejected' },
  staff:  { S: 'Staff', N: 'Non-staff', R: 'Rejected' },
  id:     { Y: 'Visible', N: 'Not Visible', R: 'Rejected' },
};

const EMPTY_ANN = { gender: null, age: null, staff: null, id: null };

/* ── Helpers ── */
function annEqual(a, b) {
  return a.gender === b.gender && a.age === b.age && a.staff === b.staff && a.id === b.id;
}

function hasUnsavedChanges(currentAnn, savedAnn) {
  /* Issue 2 fix: compare current to the image's saved labels, not just "any label set" */
  const saved = savedAnn ?? EMPTY_ANN;
  return !annEqual(currentAnn, saved);
}

/* ── Person silhouette ── */
function PersonIcon({ shape, color, size = 1 }) {
  const w = Math.round(90 * size);
  const h = Math.round(120 * size);
  if (shape === 2) return (
    <svg viewBox="0 0 80 70" fill={color} width={w} height={Math.round(80 * size)} aria-hidden="true">
      <circle cx="22" cy="14" r="9"/>
      <path d="M8 64c0-16 3-22 14-24v7l0-7c11 2 14 8 14 24z"/>
      <circle cx="58" cy="14" r="9"/>
      <path d="M44 64c0-16 3-22 14-24v7l0-7c11 2 14 8 14 24z"/>
    </svg>
  );
  if (shape === 1) return (
    <svg viewBox="0 0 60 70" fill={color} width={Math.round(70 * size)} height={h} aria-hidden="true">
      <circle cx="30" cy="15" r="8"/>
      <path d="M18 66c0-14 3-20 12-22v6l0-6c9 2 12 8 12 22z"/>
    </svg>
  );
  return (
    <svg viewBox="0 0 60 80" fill={color} width={w} height={h} aria-hidden="true">
      <circle cx="30" cy="16" r="11"/>
      <path d="M13 76c0-20 4-28 17-30v8l0-8c13 2 17 10 17 30z"/>
    </svg>
  );
}

export default function Curation() {
  const navigate = useNavigate();

  const [list, setList]       = useState(() => MOCK_IMAGES.map(m => ({ ...m })));
  const [popup, setPopup]     = useState(null);
  const [dark, setDark]       = useState(true);
  const [filter, setFilter]   = useState('all');
  const [search, setSearch]   = useState('');
  const [saveError, setSaveError] = useState(false);

  /* ── Refs — avoid all stale closures ── */
  const annRef        = useRef(EMPTY_ANN);
  const popupRef      = useRef(null);
  const listRef       = useRef(list);
  /* Issue 1: ref to first focusable element in popup for focus trap */
  const firstFocusRef = useRef(null);
  const lastFocusRef  = useRef(null);
  /* Remember which gallery card triggered the popup so we can restore focus */
  const triggerRef    = useRef(null);

  const [ann, setAnnState] = useState(EMPTY_ANN);

  const setAnn = useCallback((updater) => {
    setAnnState(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      annRef.current = next;
      return next;
    });
  }, []);

  useEffect(() => { popupRef.current = popup; }, [popup]);
  useEffect(() => { listRef.current  = list;  }, [list]);

  const curated = list.filter(i => i.curated).length;
  const pct     = Math.round((curated / list.length) * 100);

  /* ── Dark mode ── */
  useEffect(() => {
    document.documentElement.classList.toggle('cur-dark', dark);
    return () => document.documentElement.classList.remove('cur-dark');
  }, [dark]);

  /* ── Issue 1: Focus trap inside popup ── */
  useEffect(() => {
    if (!popup) return;

    /* Move focus into the popup on open */
    const raf = requestAnimationFrame(() => {
      firstFocusRef.current?.focus();
    });

    return () => cancelAnimationFrame(raf);
  }, [popup]);

  /* ── Keyboard handler — no stale closures via refs ── */
  const handleKey = useCallback((e) => {
    const currentPopup = popupRef.current;
    if (!currentPopup) return;

    /* Issue 1: Tab trapping */
    if (e.key === 'Tab') {
      const focusables = document
        .querySelector('.cur__popup')
        ?.querySelectorAll('button:not([disabled]), [tabindex]:not([tabindex="-1"])') ?? [];
      if (!focusables.length) return;
      const first = focusables[0];
      const last  = focusables[focusables.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
      }
      return;
    }

    if (e.key === 'Escape') {
      tryClose();
      return;
    }

    if (e.key === 'Enter') {
      /* Don't intercept Enter if a button inside the popup has focus */
      if (document.activeElement?.closest('.cur__popup')) return;
      doSaveAndNext();
      return;
    }

    const key = e.key.toUpperCase();
    for (const g of ANNOTATION_GROUPS) {
      for (const o of g.options) {
        if (o.shortcut.toUpperCase() === key) {
          setAnn(p => ({ ...p, [g.field]: p[g.field] === o.key ? null : o.key }));
          return;
        }
      }
    }
  }, []); // stable — uses only refs

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  /* ── Open / close ── */
  const openPopup = (img, triggerEl) => {
    triggerRef.current = triggerEl ?? null;
    setPopup(img);
    const initial = img.annotations ? { ...img.annotations } : { ...EMPTY_ANN };
    setAnn(initial);
    setSaveError(false);
  };

  /* Issue 2 fix: only warn if current selections differ from the image's saved labels */
  const tryClose = () => {
    const current = annRef.current;
    const saved   = popupRef.current?.annotations ?? null;
    if (hasUnsavedChanges(current, saved)) {
      if (!window.confirm('You have unsaved changes. Discard and close?')) return;
    }
    closePopup();
  };

  const closePopup = () => {
    setPopup(null);
    /* Issue 1: restore focus to the card that opened the popup */
    setTimeout(() => triggerRef.current?.focus(), 0);
  };

  const closeViaBackdrop = (e) => {
    if (e.target === e.currentTarget) tryClose();
  };

  const toggle = (field, key) =>
    setAnn(p => ({ ...p, [field]: p[field] === key ? null : key }));

  /* ── Save & Next — all from refs ── */
  const doSaveAndNext = useCallback(() => {
    const currentPopup = popupRef.current;
    const currentAnn   = annRef.current;
    if (!currentPopup) return;

    const hasAnn = Object.values(currentAnn).some(v => v !== null);
    if (!hasAnn) {
      setSaveError(true);
      setTimeout(() => setSaveError(false), 2500);
      return;
    }
    setSaveError(false);

    const savedAnn = { ...currentAnn };
    setList(prev => {
      const updated = prev.map(img =>
        img.id === currentPopup.id ? { ...img, curated: true, annotations: savedAnn } : img
      );
      listRef.current = updated;
      return updated;
    });

    const idx  = listRef.current.findIndex(i => i.id === currentPopup.id);
    const next = listRef.current.slice(idx + 1).find(i => !i.curated);
    if (next) {
      openPopup(next);
    } else {
      closePopup();
    }
  }, []); // stable

  /* ── Accept all suggestions ── */
  const acceptAll = () => {
    setAnn({
      gender: popup?.gender === 'Male' ? 'M' : 'F',
      age:    '4',
      staff:  'N',
      id:     'N',
    });
  };

  /* ── Filtered list ── */
  const filtered = list.filter(img => {
    if (filter === 'curated' && !img.curated) return false;
    if (filter === 'pending' && img.curated)  return false;
    if (search && !img.label.toLowerCase().includes(search.toLowerCase()) &&
        !img.location.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const palette = (img) => dark
    ? { bg: img.palette.dark_bg, fg: img.palette.dark_fg }
    : { bg: img.palette.bg,      fg: img.palette.fg };

  return (
    <div className={`cur${dark ? ' cur--dark' : ''}`}>

      {/* ── Topbar ── */}
      <header className="cur__bar">
        <div className="cur__bar-left">
          <div className="cur__brand">
            <div className="cur__brand-icon" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#fff" strokeWidth="2"/>
                <path d="M8 12l3 3 5-5" stroke="#60a5fa" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="cur__brand-text">OLY VISION</span>
          </div>
          <button className="cur__bar-btn" onClick={() => navigate('/')}>← Dashboard</button>
          <button className="cur__bar-btn" onClick={() => navigate('/training')}>Training</button>
        </div>

        <div className="cur__bar-center">
          <span className="cur__stat-label">Curated</span>
          <span className="cur__stat-badge" aria-live="polite">{curated} / {list.length}</span>
          <div className="cur__bar-prog-wrap" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
            <div className="cur__bar-prog-fill" style={{ width: `${pct}%` }} />
          </div>
          <span className="cur__stat-pct">{pct}%</span>
        </div>

        <div className="cur__bar-right">
          <button className="cur__theme-toggle" onClick={() => setDark(d => !d)}
            aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}>
            {dark ? '☀️' : '🌙'}
            <span>{dark ? 'Light' : 'Dark'}</span>
          </button>
          <div className="cur__bar-user" aria-label="Signed in as admin">
            <div className="cur__bar-avatar" aria-hidden="true">A</div>
            <span className="cur__bar-name">admin</span>
          </div>
        </div>
      </header>

      {/* ── Gallery controls ── */}
      <div className="cur__controls">
        <div className="cur__search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            id="gallery-search"
            className="cur__search"
            placeholder="Search by ID or location…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            aria-label="Search images by ID or location"
          />
        </div>
        <div className="cur__filters" role="group" aria-label="Filter images">
          {['all', 'curated', 'pending'].map(f => (
            <button key={f}
              className={`cur__filter-btn${filter === f ? ' cur__filter-btn--active' : ''}`}
              onClick={() => setFilter(f)}
              aria-pressed={filter === f}>
              {f === 'all'     && `All (${list.length})`}
              {f === 'curated' && `✅ Curated (${curated})`}
              {f === 'pending' && `⏳ Pending (${list.length - curated})`}
            </button>
          ))}
        </div>
      </div>

      {/* ── Gallery grid ── */}
      {/* Issue 1 fix: ul > li > button is valid HTML and preserves button role for screen readers */}
      <ul className="cur__gallery" role="list">
        {filtered.map(img => {
          const p = palette(img);
          const a = img.annotations;
          return (
            <li key={img.id} role="listitem">
              <button
                className={`cur__card${img.curated ? ' cur__card--curated' : ''}`}
                onClick={e => openPopup(img, e.currentTarget)}
                aria-label={`${img.label} — ${img.location}${img.curated ? ' (annotated)' : ' (pending)'}`}
              >
                <div className="cur__card-img" style={{ background: `${p.bg}33` }}>
                  <PersonIcon shape={img.shape} color={p.fg} size={0.7} />
                  {img.curated && <div className="cur__card-check" aria-hidden="true">✅</div>}
                  {img.curated && a && (
                    <div className="cur__card-tooltip" role="tooltip">
                      <div className="cur__tooltip-row">
                        <span className="cur__tooltip-key">Gender</span>
                        <span className="cur__tooltip-val">{ANN_LABELS.gender[a.gender] || '—'}</span>
                      </div>
                      <div className="cur__tooltip-row">
                        <span className="cur__tooltip-key">Age</span>
                        <span className="cur__tooltip-val">{ANN_LABELS.age[a.age] || '—'}</span>
                      </div>
                      <div className="cur__tooltip-row">
                        <span className="cur__tooltip-key">Staff</span>
                        <span className="cur__tooltip-val">{ANN_LABELS.staff[a.staff] || '—'}</span>
                      </div>
                      <div className="cur__tooltip-row">
                        <span className="cur__tooltip-key">ID</span>
                        <span className="cur__tooltip-val">{ANN_LABELS.id[a.id] || '—'}</span>
                      </div>
                    </div>
                  )}
                </div>
                <div className="cur__card-footer">
                  <span className="cur__card-label">{img.label}</span>
                  <span className="cur__card-loc">{img.location}</span>
                </div>
              </button>
            </li>
          );
        })}
        {filtered.length === 0 && (
          <li className="cur__gallery-empty">No images match your filter</li>
        )}
      </ul>

      {/* ── Annotation Popup ── */}
      {popup && (
        <div
          className="cur__overlay"
          onClick={closeViaBackdrop}
          role="dialog"
          aria-modal="true"
          aria-label={`Annotate ${popup.label}`}
        >
          <div className="cur__popup">

            {/* Left — image */}
            <div className="cur__popup-img" style={{ background: `${palette(popup).bg}44` }}>
              <button
                ref={firstFocusRef}
                className="cur__popup-arrow cur__popup-arrow--left"
                aria-label="Previous image"
                onClick={e => {
                  e.stopPropagation();
                  const idx = listRef.current.findIndex(i => i.id === popup.id);
                  if (idx > 0) openPopup(listRef.current[idx - 1]);
                }}
              >‹</button>
              <button
                className="cur__popup-arrow cur__popup-arrow--right"
                aria-label="Next image"
                onClick={e => {
                  e.stopPropagation();
                  const idx = listRef.current.findIndex(i => i.id === popup.id);
                  if (idx < listRef.current.length - 1) openPopup(listRef.current[idx + 1]);
                }}
              >›</button>

              <div className="cur__popup-scene">
                <div className="cur__popup-wall"  style={{ background: palette(popup).fg + '08' }} />
                <div className="cur__popup-floor" style={{ background: palette(popup).fg + '15' }} />
                <div className="cur__popup-person">
                  <PersonIcon shape={popup.shape} color={palette(popup).fg} size={1.6} />
                </div>
                <div className="cur__popup-bbox" style={{ borderColor: palette(popup).fg + '90' }} aria-hidden="true"/>
              </div>

              <div className="cur__popup-img-meta">
                <span className="cur__popup-img-label">{popup.label}</span>
                <span className="cur__popup-img-loc">📍 {popup.location}</span>
                <span className="cur__popup-img-nav">
                  {listRef.current.findIndex(i => i.id === popup.id) + 1} / {listRef.current.length}
                </span>
              </div>
            </div>

            {/* Right — annotation panel */}
            <div className="cur__popup-panel">
              <div className="cur__popup-panel-hd">
                <span className="cur__popup-panel-title" id="popup-title">Annotations</span>
                <button
                  className="cur__popup-close"
                  onClick={tryClose}
                  aria-label="Close annotation popup"
                >✕</button>
              </div>

              <div className="cur__popup-groups" aria-labelledby="popup-title">
                {ANNOTATION_GROUPS.map(g => (
                  <div key={g.field} className="cur__popup-group">
                    <div className="cur__popup-group-hd">
                      <span className="cur__popup-group-icon" aria-hidden="true">{g.icon}</span>
                      <span className="cur__popup-group-title" id={`group-${g.field}`}>{g.title}</span>
                    </div>
                    <div className="cur__popup-opts" role="group" aria-labelledby={`group-${g.field}`}>
                      {g.options.map(o => (
                        <button
                          key={o.key}
                          className={`cur__popup-opt${ann[g.field] === o.key ? ' cur__popup-opt--active' : ''}${o.isReject ? ' cur__popup-opt--reject' : ''}`}
                          style={{ '--opt-color': o.color }}
                          onClick={() => toggle(g.field, o.key)}
                          aria-pressed={ann[g.field] === o.key}
                          title={`Shortcut: ${o.shortcut}`}
                        >
                          {o.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="cur__popup-actions">
                {saveError && (
                  <div className="cur__popup-save-error" role="alert">
                    ⚠ Select at least one annotation before saving
                  </div>
                )}
                <div className="cur__popup-actions-row">
                  <button className="cur__popup-save-next" onClick={doSaveAndNext}>
                    Save &amp; next →
                  </button>
                  <button
                    ref={lastFocusRef}
                    className="cur__popup-accept-all"
                    onClick={acceptAll}
                  >
                    Accept all suggestions ✓
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
