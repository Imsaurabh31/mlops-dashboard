import { useState, useEffect, useCallback } from 'react';
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
const AGES      = ['Adult', 'Teen', 'Child', 'Mature', 'Unknown'];

/* Pre-set annotations for the already-curated images */
const PRESET_ANN = [
  { gender: 'M', age: '4', staff: 'N', id: 'N' },
  { gender: 'F', age: '5', staff: 'S', id: 'Y' },
  { gender: 'M', age: '3', staff: 'N', id: 'N' },
  { gender: 'F', age: '4', staff: 'N', id: 'N' },
  { gender: 'M', age: '5', staff: 'S', id: 'Y' },
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
  timestamp: `2026-10-${String(28 - (i % 3)).padStart(2,'0')} ${String(10 + (i % 12)).padStart(2,'0')}:${String(i * 3 % 60).padStart(2,'0')}`,
}));

const ANNOTATION_GROUPS = [
  {
    field: 'gender', title: 'Gender', keys: ['M','F'],
    options: [
      { key: 'M', label: 'Male',   shortcut: 'M' },
      { key: 'F', label: 'Female', shortcut: 'F' },
    ],
  },
  {
    field: 'age', title: 'Age Category', keys: ['1–5'], grid: true,
    options: [
      { key: '1', label: 'Infant',  shortcut: '1' },
      { key: '2', label: 'Child',   shortcut: '2' },
      { key: '3', label: 'Teen',    shortcut: '3' },
      { key: '4', label: 'Adult',   shortcut: '4' },
      { key: '5', label: 'Mature',  shortcut: '5' },
      { key: '6', label: 'Unknown', shortcut: '6' },
    ],
  },
  {
    field: 'staff', title: 'Staff Member', keys: ['S','N'],
    options: [
      { key: 'S', label: 'Yes – Staff',   shortcut: 'S' },
      { key: 'N', label: 'No – Customer', shortcut: 'N' },
    ],
  },
  {
    field: 'id', title: 'ID Card Visible', keys: ['Y','N'],
    options: [
      { key: 'Y', label: 'Yes – Visible', shortcut: 'Y' },
      { key: 'N', label: 'No – Hidden',   shortcut: 'H' },
    ],
  },
];

const ANN_LABELS = {
  gender: { M: 'Male', F: 'Female' },
  age:    { '1':'Infant','2':'Child','3':'Teen','4':'Adult','5':'Mature','6':'Unknown' },
  staff:  { S: 'Staff', N: 'Customer' },
  id:     { Y: 'ID Visible', N: 'ID Hidden' },
};

/* ── Person silhouette ── */
function PersonIcon({ shape, color, size = 1 }) {
  const w = Math.round(90 * size);
  const h = Math.round(120 * size);
  if (shape === 2) return (
    <svg viewBox="0 0 80 70" fill={color} width={w} height={Math.round(80 * size)}>
      <circle cx="22" cy="14" r="9"/>
      <path d="M8 64c0-16 3-22 14-24v7l0-7c11 2 14 8 14 24z"/>
      <circle cx="58" cy="14" r="9"/>
      <path d="M44 64c0-16 3-22 14-24v7l0-7c11 2 14 8 14 24z"/>
    </svg>
  );
  if (shape === 1) return (
    <svg viewBox="0 0 60 70" fill={color} width={Math.round(70 * size)} height={h}>
      <circle cx="30" cy="15" r="8"/>
      <path d="M18 66c0-14 3-20 12-22v6l0-6c9 2 12 8 12 22z"/>
    </svg>
  );
  return (
    <svg viewBox="0 0 60 80" fill={color} width={w} height={h}>
      <circle cx="30" cy="16" r="11"/>
      <path d="M13 76c0-20 4-28 17-30v8l0-8c13 2 17 10 17 30z"/>
    </svg>
  );
}

export default function Curation() {
  const navigate = useNavigate();

  const [list, setList]       = useState(() => MOCK_IMAGES.map(m => ({ ...m })));
  const [popup, setPopup]     = useState(null);   // image currently in popup
  const [ann, setAnn]         = useState({ gender: null, age: null, staff: null, id: null });
  const [dark, setDark]       = useState(false);
  const [filter, setFilter]   = useState('all'); // all | curated | pending
  const [search, setSearch]   = useState('');

  const curated = list.filter(i => i.curated).length;
  const pct     = Math.round((curated / list.length) * 100);

  /* Apply dark class to root */
  useEffect(() => {
    document.documentElement.classList.toggle('cur-dark', dark);
    return () => document.documentElement.classList.remove('cur-dark');
  }, [dark]);

  /* Keyboard shortcuts inside popup */
  const handleKey = useCallback((e) => {
    if (!popup) return;
    const key = e.key.toUpperCase();
    for (const g of ANNOTATION_GROUPS) {
      for (const o of g.options) {
        if (o.shortcut.toUpperCase() === key) {
          setAnn(p => ({ ...p, [g.field]: p[g.field] === o.key ? null : o.key }));
          return;
        }
      }
    }
    if (e.key === 'Enter') saveAndNext();
    if (e.key === 'Escape') setPopup(null);
  }, [popup, ann]); // eslint-disable-line

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  const openPopup = (img) => {
    setPopup(img);
    setAnn(img.annotations ? { ...img.annotations } : { gender: null, age: null, staff: null, id: null });
  };

  const closePopup = () => setPopup(null);

  const toggle = (field, key) =>
    setAnn(p => ({ ...p, [field]: p[field] === key ? null : key }));

  const saveAndNext = () => {
    if (!popup) return;
    const savedAnn = { ...ann };
    setList(prev => prev.map(img =>
      img.id === popup.id ? { ...img, curated: true, annotations: savedAnn } : img
    ));
    // advance to next uncurated
    const idx  = list.findIndex(i => i.id === popup.id);
    const next = list.slice(idx + 1).find(i => !i.curated);
    if (next) { setPopup(next); setAnn({ gender: null, age: null, staff: null, id: null }); }
    else setPopup(null);
  };

  /* Filtered list */
  const filtered = list.filter(img => {
    if (filter === 'curated' && !img.curated) return false;
    if (filter === 'pending' && img.curated)  return false;
    if (search && !img.label.toLowerCase().includes(search.toLowerCase()) &&
        !img.location.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const palette = (img) => dark
    ? { bg: img.palette.dark_bg, fg: img.palette.dark_fg }
    : { bg: img.palette.bg,      fg: img.palette.fg      };

  return (
    <div className={`cur${dark ? ' cur--dark' : ''}`}>

      {/* ══════════ TOPBAR ══════════ */}
      <header className="cur__bar">
        <div className="cur__bar-left">
          <div className="cur__brand">
            <div className="cur__brand-icon">
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
          <span className="cur__stat-badge">{curated} / {list.length}</span>
          <div className="cur__bar-prog-wrap">
            <div className="cur__bar-prog-fill" style={{ width: `${pct}%` }} />
          </div>
          <span className="cur__stat-pct">{pct}%</span>
        </div>

        <div className="cur__bar-right">
          {/* Dark / Light toggle */}
          <button
            className="cur__theme-toggle"
            onClick={() => setDark(d => !d)}
            title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {dark ? '☀️' : '🌙'}
            <span>{dark ? 'Light' : 'Dark'}</span>
          </button>
          <div className="cur__bar-user">
            <div className="cur__bar-avatar">A</div>
            <span className="cur__bar-name">admin</span>
          </div>
        </div>
      </header>

      {/* ══════════ GALLERY CONTROLS ══════════ */}
      <div className="cur__controls">
        <div className="cur__search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            className="cur__search"
            placeholder="Search by ID or location…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div className="cur__filters">
          {['all', 'curated', 'pending'].map(f => (
            <button
              key={f}
              className={`cur__filter-btn${filter === f ? ' cur__filter-btn--active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all'     && `All (${list.length})`}
              {f === 'curated' && `✅ Curated (${curated})`}
              {f === 'pending' && `⏳ Pending (${list.length - curated})`}
            </button>
          ))}
        </div>
      </div>

      {/* ══════════ GALLERY GRID ══════════ */}
      <div className="cur__gallery">
        {filtered.map(img => {
          const p   = palette(img);
          const ann = img.annotations;
          return (
            <div
              key={img.id}
              className={`cur__card${img.curated ? ' cur__card--curated' : ''}`}
              onClick={() => openPopup(img)}
            >
              {/* Image area — fully transparent, gradient shows through */}
              <div
                className="cur__card-img"
                style={{
                  background: `${p.bg}33`,
                }}
              >
                <PersonIcon shape={img.shape} color={p.fg} size={0.7} />

                {/* ✅ Annotated overlay */}
                {img.curated && (
                  <div className="cur__card-check">✅</div>
                )}

                {/* Hover tooltip — only for annotated images */}
                {img.curated && ann && (
                  <div className="cur__card-tooltip">
                    <div className="cur__tooltip-row">
                      <span className="cur__tooltip-key">Gender</span>
                      <span className="cur__tooltip-val">{ANN_LABELS.gender[ann.gender] || '—'}</span>
                    </div>
                    <div className="cur__tooltip-row">
                      <span className="cur__tooltip-key">Age</span>
                      <span className="cur__tooltip-val">{ANN_LABELS.age[ann.age] || '—'}</span>
                    </div>
                    <div className="cur__tooltip-row">
                      <span className="cur__tooltip-key">Staff</span>
                      <span className="cur__tooltip-val">{ANN_LABELS.staff[ann.staff] || '—'}</span>
                    </div>
                    <div className="cur__tooltip-row">
                      <span className="cur__tooltip-key">ID</span>
                      <span className="cur__tooltip-val">{ANN_LABELS.id[ann.id] || '—'}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Card footer */}
              <div className="cur__card-footer">
                <span className="cur__card-label">{img.label}</span>
                <span className="cur__card-loc">{img.location}</span>
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="cur__gallery-empty">
            <span>No images match your filter</span>
          </div>
        )}
      </div>

      {/* ══════════ ANNOTATION POPUP ══════════ */}
      {popup && (
        <div className="cur__overlay" onClick={closePopup}>
          <div className="cur__popup" onClick={e => e.stopPropagation()}>

            {/* Popup header */}
            <div className="cur__popup-hd">
              <div className="cur__popup-title-group">
                <span className="cur__popup-label">{popup.label}</span>
                <span className="cur__popup-loc">📍 {popup.location}</span>
                <span className="cur__popup-time">🕐 {popup.timestamp}</span>
              </div>
              <div className="cur__popup-hd-right">
                <span className="cur__popup-nav">
                  {list.findIndex(i => i.id === popup.id) + 1} / {list.length}
                </span>
                <button className="cur__popup-close" onClick={closePopup}>✕</button>
              </div>
            </div>

            <div className="cur__popup-body">

              {/* Image preview */}
              <div className="cur__popup-img" style={{ background: `${palette(popup).bg}44` }}>
                <div className="cur__popup-scene">
                  <div className="cur__popup-wall"  style={{ background: palette(popup).fg + '08' }} />
                  <div className="cur__popup-floor" style={{ background: palette(popup).fg + '15' }} />
                  <div className="cur__popup-person">
                    <PersonIcon shape={popup.shape} color={palette(popup).fg} size={1.4} />
                  </div>
                  <div className="cur__popup-bbox" style={{ borderColor: palette(popup).fg + '90' }} />
                  {popup.curated && <div className="cur__popup-curated-badge">✅ Annotated</div>}
                </div>
              </div>

              {/* Annotation panel */}
              <div className="cur__popup-panel">
                <p className="cur__popup-panel-hint">
                  Select annotations below or use keyboard shortcuts
                </p>

                {ANNOTATION_GROUPS.map(g => (
                  <div key={g.field} className="cur__popup-group">
                    <div className="cur__popup-group-hd">
                      <span className="cur__popup-group-title">{g.title}</span>
                      <div className="cur__popup-keys">
                        {g.keys.map(k => <span key={k} className="cur__kbdkey">{k}</span>)}
                      </div>
                    </div>
                    <div className={`cur__popup-opts${g.grid ? ' cur__popup-opts--grid' : ''}`}>
                      {g.options.map(o => (
                        <button
                          key={o.key}
                          className={`cur__popup-opt${ann[g.field] === o.key ? ' cur__popup-opt--active' : ''}`}
                          onClick={() => toggle(g.field, o.key)}
                        >
                          <span className="cur__popup-opt-label">{o.label}</span>
                          <span className="cur__kbdkey cur__kbdkey--sm">{o.shortcut}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                <div className="cur__popup-actions">
                  <button className="cur__popup-skip" onClick={closePopup}>Skip</button>
                  <button className="cur__popup-save" onClick={saveAndNext}>
                    Save &amp; Next
                    <span className="cur__kbdkey cur__kbdkey--dark">Enter</span>
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
