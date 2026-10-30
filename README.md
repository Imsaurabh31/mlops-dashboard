# OLY VISION — MLOps Dashboard

A recreation of the OLY VISION MLOps Dashboard built with **React + Vite**. This is Stage 1 of the MLOps platform rebuild.

---

## 🚀 Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📸 Pages

### 1. Dashboard
- Live stat cards — Total Images, Curated, Pending, Active Users
- Quick action cards to navigate to each section
- Recent activity table with colored status badges
- Pipeline health bars showing model accuracy
- System status indicators and storage donut chart

### 2. Curation (Gallery)
- Gallery grid layout — all images displayed at once
- Annotated images show a ✅ overlay
- Hover tooltip on annotated images showing Gender, Age, Staff and ID Card data
- Click any image to open annotation popup with blurred background
- Annotation controls for Gender, Age Category, Staff Member and ID Card Visible
- Save & Next auto-advances to the next unannotated image
- Search by image ID or location
- Filter pills — All / Curated / Pending
- Light and Dark mode toggle
- **Apple Liquid Glass theme** — animated gradient background with frosted glass cards

### 3. Admin Panel
- 5 live stat cards that update when batches are created or deleted
- Batch Assignments table with progress bars and color-coded statuses
- Full CRUD — Create, Edit, Delete batches
- Create Batch form with live validation and duplicate name check
- User Management table with role badges and active/inactive status
- Progress Overview with per-curator performance bars

### 4. Model Training
- Model cards for Gender Classification, Age Classification and Staff Detection
- Training simulation with animated progress bar
- Three tabs — Training Jobs, Experiments, Deployed Models

---

## 🎨 Design System

- **Theme** — IAM-style light theme with Apple Liquid Glass on Curation page
- **Sidebar** — Dark navy fixed sidebar navigation
- **Topbar** — White topbar with breadcrumbs, search and user info
- **Color tokens** — All design tokens defined in `src/index.css`
- **Shared components** — `.badge`, `.btn`, `.card`, `.tbl`, `.chip` reused across all pages
- **Fonts** — Inter (Google Fonts)

---

## 🛠 Tech Stack

| Tool | Version |
|------|---------|
| React | 18.3.1 |
| Vite | 5.4.8 |
| React Router DOM | 6.26.1 |

---

## 📁 Project Structure

```
src/
├── components/
│   ├── Sidebar.jsx / .css      ← Dark navy sidebar navigation
│   ├── Topbar.jsx / .css       ← White topbar with breadcrumbs
│   └── Layout.jsx / .css       ← Shared page wrapper
├── pages/
│   ├── Dashboard.jsx / .css    ← Main dashboard
│   ├── Curation.jsx / .css     ← Gallery annotation tool
│   ├── Training.jsx / .css     ← Model training page
│   └── Admin.jsx / .css        ← Admin panel with CRUD
├── index.css                   ← Global design tokens
├── App.jsx                     ← Router setup
└── main.jsx                    ← Entry point
```

---

## ✅ Stage 1 Checklist

- [x] Dashboard with live stats and activity feed
- [x] Curation gallery with annotation popup
- [x] Admin panel with full CRUD
- [x] Model training page with simulation
- [x] Light / Dark mode on Curation
- [x] Apple Liquid Glass theme on Curation
- [x] Responsive layout

---

## 🔜 Stage 2 — Coming Next

- Model auto training pipeline
- Real-time training progress with live metrics
- Experiment tracking
- Auto deployment on accuracy threshold

---

Built by **Saurabh Kumar**
