# NeuroFlow Design System

Design patterns, reusable components, and UI guidelines for NeuroFlow mockups and frontend pages.

NeuroFlow is a **facilitation portal** for neuroscience medical image processing: **one web module per CLI tool**. Each tool page covers upload, parameters, command preview, execution status, and logs.

**Stack:** plain HTML/CSS, **Tailwind CSS** (built in `frontend/`), **Material Design 3 (MD3)** tokens, **Inter** + **Manrope**, **Material Symbols Outlined**.

**Production pages:** `frontend/src/pages/index.html` (hub), `frontend/src/pages/tools/freesurfer.html` (reference tool module).

**Legacy mockups:** `doc/mockup/` (older portal concepts; do not use `pipelines.html` — removed).

**Project standards:** `.cursor/rules/project-pattern.mdc`.

---

## Table of Contents

1. [Design principles](#design-principles)
2. [MD3 foundation](#md3-foundation)
3. [Page structure](#page-structure)
4. [Reusable components](#reusable-components)
5. [Typography](#typography)
6. [Color tokens](#color-tokens)
7. [Layout patterns](#layout-patterns)
8. [Uniformity checklist](#uniformity-checklist)
9. [References](#references)
10. [Changelog](#changelog)

---

## Design principles

- **Clarity over density** — workflows should be obvious to researchers and clinicians.
- **Data-first** — subject ID, job status, and CLI output before decorative UI.
- **English UI copy** by default; localization may be added later.
- **Accessible defaults** — semantic HTML, visible labels, keyboard-friendly forms and tables.
- **Simple frontend** — no heavy SPA unless explicitly required; reuse shared chrome (sidebar, top bar) across pages.
- **MD3 tokens** — prefer theme colors (`primary`, `outline-variant`, `surface-*`) over ad-hoc palette classes in new work.

---

## MD3 foundation

NeuroFlow uses **Material Design 3** with custom color tokens defined in each page’s Tailwind config (see `doc/mockup/home.html`).

| Layer | Choice |
|-------|--------|
| CSS | Tailwind CSS (CDN in mockups; build step optional later) |
| Typography | Inter (body), Manrope (headlines) |
| Icons | Material Symbols Outlined (24px optical size) |
| Responsiveness | Mobile-first; primary breakpoint `md:` (768px+) |

---

## Page structure

### Standard shell (hub / package / help pages)

Production chrome is rendered by `frontend/src/js/hub-layout.js` (not the legacy mockup pipeline block).

```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR (256px / w-64 fixed)  │  TOP BAR (h-16)    │
│  ├─ Facilitation portal label  │  ├─ Page title     │
│  ├─ Home / History / packages  │  ├─ Help (→ /help/)│
│  ├─ Help (user wiki)           │  └─ Open API       │
│  └─ Open API (Swagger /docs)   │                    │
├─────────────────────────────────────────────────────┤
│  MAIN (ml-64, pt-24, max-width 1400px, centered)      │
└─────────────────────────────────────────────────────┘
```

**Help vs Open API:** sidebar **Help** and the header `help_outline` link open the in-app user wiki at `/help/`. **Open API** opens FastAPI Swagger at `/docs`. Do not label Swagger as the user guide.

**Help wiki pages** (`frontend/src/pages/help/`): same hub shell; topic nav via `help-layout.js` (`#help-wiki-nav`); article column `max-w-3xl`.
### Default dimensions

| Region | Tailwind / size |
|--------|------------------|
| Sidebar | `w-64`, `h-full`, `fixed left-0 top-0`, `py-6`, `border-r border-outline-variant`; logo `/assets/neuroflow_logo.png` |
| Top bar | `h-16`, `fixed top-0 right-0`, `w-[calc(100%-16rem)]`, `px-8` |
| Hub main | `ml-64 pt-24 pb-16 px-12`, inner `max-w-[1400px] mx-auto` |
| Tool page main | `max-w-[800px]` centered (unchanged) |

### Tool module page (production pattern)

Reference: `frontend/src/pages/tools/freesurfer.html`.

| Section | Purpose |
|---------|---------|
| Top nav | Logo, module name, Help link to `/help/`, link back to package (where applicable) |
| Header | Package/module title, summary, vendor **Official documentation** plus **NeuroFlow guide** |
| Input | Multi-file drag-and-drop; per-file Subject ID table when batching |
| Configuration | Simple CLI flags only (e.g. recon stage when not fixed via `?module=`) |
| Execute | Primary CTA; heuristic `N × hours` estimate below button |
| Status panel | Log tail, elapsed time, batch position, heuristic ETA, PID |

Hub (`index.html`) table columns: **Package** | **Module** | Description | Status | Action. Rows from `GET /api/v1/modules`; action links to `/tools/<page>?module=<id>`. Toolbar: global search, per-column filters (package, module, status), sortable headers. Shared chrome via `frontend/src/js/hub-layout.js`.

Home also has a **Workspaces** panel (above Active processes): create project/user folders, list existing workspaces under `NEUROFLOW_DATASETS_ROOT`, **Use** (persists name in `localStorage`), and **Open folder** (host file manager via API).

Dataset layout is **subject-centered**: under each workspace, inputs and tool outputs live under `sub-<id>/` (including `sub-<id>/derivatives/<package>/<module>/`) so processings stay traceable per subject.

Package pages (`frontend/src/pages/packages/<id>.html`): list modules for one package; sidebar highlights package; FreeSurfer links to official docs.

---

## Reusable components

### 1. Sidebar (fixed on every page)

```html
<aside class="fixed left-0 top-0 h-full w-64 border-r border-outline-variant bg-surface-container-low flex flex-col py-6 z-50">
  <div class="px-6 mb-8">
    <img alt="NeuroFlow logo" class="h-10 w-auto" src="../../assets/images/neuroflow_logo.png"/>
    <p class="text-[10px] uppercase tracking-widest text-on-surface-variant font-bold mt-1">Clinical v2.4.0</p>
  </div>

  <nav class="flex-1 space-y-1" aria-label="Main navigation">
    <!-- Nav items — see patterns below -->
  </nav>

  <div class="px-4 mb-4">
    <a class="w-full bg-primary text-white py-2.5 rounded-lg font-label-sm flex items-center justify-center gap-2 hover:opacity-90 transition-all active:scale-95" href="./pipelines.html">
      <span class="material-symbols-outlined text-sm" aria-hidden="true">play_arrow</span>
      Run Pipeline
    </a>
  </div>

  <div class="border-t border-outline-variant pt-4 space-y-1">
    <!-- Documentation, Settings, profile -->
  </div>
</aside>
```

#### Navigation item

**Inactive:**

```html
<a class="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container hover:text-primary transition-all duration-200 active:scale-95" href="#">
  <span class="material-symbols-outlined" aria-hidden="true">icon_name</span>
  <span class="font-label-sm">Label</span>
</a>
```

**Active:**

```html
<a class="flex items-center gap-3 px-4 py-3 border-l-4 border-primary bg-primary-fixed/30 text-primary font-semibold transition-all duration-200 active:scale-95" href="#" aria-current="page">
  <span class="material-symbols-outlined text-primary" aria-hidden="true">icon_name</span>
  <span class="font-label-sm">Label</span>
</a>
```

**Rules:**

- Active indicator: `border-l-4 border-primary` (always `primary`, never another accent).
- Active background: light primary tint (e.g. `bg-primary-fixed/30` or `bg-blue-50` in legacy mockups).
- Active text: `text-primary font-semibold`.

#### Profile block

```html
<div class="px-4 py-3 flex items-center gap-3 mt-2">
  <img alt="User profile" class="w-8 h-8 rounded-full border border-outline-variant" src="[URL]"/>
  <div class="overflow-hidden">
    <p class="text-xs font-semibold text-on-surface truncate">Dr. Aris Thorne</p>
    <p class="text-[10px] text-on-surface-variant">Neuroradiology</p>
  </div>
</div>
```

---

### 2. Top bar (fixed on every page)

```html
<header class="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 bg-white/80 backdrop-blur-md z-40 flex justify-between items-center px-8 border-b border-outline-variant shadow-sm">
  <div class="flex items-center gap-4 flex-1">
    <label class="relative w-full max-w-md">
      <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm" aria-hidden="true">search</span>
      <input class="w-full bg-surface-container-low border-outline-variant rounded-full pl-10 pr-4 py-1.5 text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all" placeholder="Search subjects, sessions, or runs…" type="search"/>
    </label>
  </div>

  <div class="flex items-center gap-6">
    <div class="flex items-center gap-4 text-on-surface-variant">
      <button type="button" class="hover:text-primary transition-colors active:scale-95" aria-label="Notifications">
        <span class="material-symbols-outlined" aria-hidden="true">notifications_active</span>
      </button>
      <button type="button" class="hover:text-primary transition-colors active:scale-95" aria-label="Help">
        <span class="material-symbols-outlined" aria-hidden="true">help_outline</span>
      </button>
    </div>

    <div class="h-6 w-px bg-outline-variant" role="separator"></div>

    <button type="button" class="bg-primary text-white px-4 py-1.5 rounded-lg text-sm font-semibold hover:opacity-90 transition-all active:scale-95">
      Export
    </button>
  </div>
</header>
```

---

### 3. Card (bento style)

```html
<div class="p-6 rounded-xl bg-surface-container-lowest border border-outline-variant shadow-[0px_4px_12px_rgba(13,92,150,0.08)] flex flex-col group transition-all hover:border-primary-container">
  <div class="flex justify-between items-start mb-4">
    <div class="p-2 bg-primary-fixed rounded-lg text-primary">
      <span class="material-symbols-outlined text-2xl" aria-hidden="true">icon_name</span>
    </div>
    <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary" type="checkbox" aria-label="Select item"/>
  </div>

  <h3 class="font-headline-md text-headline-md mb-1">Title</h3>
  <p class="font-label-sm text-on-surface-variant mb-4">Description</p>

  <div class="mt-auto">
    <span class="px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container text-[12px] font-bold">Validated</span>
  </div>
</div>
```

**Usage:**

- Badges: `rounded-full`, `px-2 py-0.5`.
- Status colors: MD3 containers (`secondary-container`, `error-container`, etc.).
- Hover: `hover:border-primary-container`.

---

### 4. Buttons

```html
<!-- Primary (main CTA) -->
<button type="button" class="bg-primary text-white px-4 py-2 rounded-lg font-semibold hover:opacity-90 transition-all active:scale-95">
  Action
</button>

<!-- Secondary -->
<button type="button" class="bg-secondary text-white px-4 py-2 rounded-lg font-semibold hover:opacity-90 transition-all active:scale-95">
  Action
</button>

<!-- Tertiary -->
<button type="button" class="border border-outline-variant text-on-surface-variant px-4 py-2 rounded-lg font-semibold hover:bg-surface-container-low transition-all active:scale-95">
  Action
</button>
```

---

## Typography

### Scale

| Role | Font | Weight | Size | Use |
|------|------|--------|------|-----|
| Headline XL | Manrope | 700 | 40px | Page titles |
| Headline LG | Manrope | 600 | 32px | Section titles |
| Headline MD | Manrope | 600 | 24px | Subsections |
| Body LG | Inter | 400 | 18px | Long-form text |
| Body MD | Inter | 400 | 16px | Default body |
| Label SM | Inter | 500 | 14px | Nav, buttons |
| Code | Monospace | 400 | 14px | Paths, CLI, JSON snippets |

### Tailwind classes

```html
<h1 class="font-headline-xl text-headline-xl">Title</h1>
<h3 class="font-headline-md text-headline-md">Subtitle</h3>
<p class="font-body-md text-body-md">Body text</p>
<span class="font-label-sm text-label-sm">Label</span>
```

Use monospace for BIDS paths (e.g. `sub-01/ses-pre/anat/sub-01_T1w.nii.gz`) in tables and detail panels.

---

## Color tokens

### MD3 palette (Tailwind `theme.extend.colors`)

```javascript
{
  primary: "#004473",
  "primary-container": "#0d5c96",
  "primary-fixed": "#d0e4ff",
  "primary-fixed-dim": "#9ccaff",

  secondary: "#006c46",
  "secondary-container": "#6af9b5",
  "secondary-fixed": "#6dfcb8",

  tertiary: "#004664",
  "tertiary-container": "#005f85",
  "tertiary-fixed": "#c6e7ff",

  surface: "#f7f9fb",
  "surface-container-low": "#f2f4f6",
  "surface-container": "#eceef0",
  "surface-container-high": "#e6e8ea",
  "surface-container-lowest": "#ffffff",

  outline: "#717781",
  "outline-variant": "#c1c7d1",

  error: "#ba1a1a",
  "error-container": "#ffdad6",

  "on-surface": "#191c1e",
  "on-surface-variant": "#414750",
  "on-secondary-container": "#007149",
}
```

### Usage rules

| Token | Use |
|-------|-----|
| `primary` | CTAs, active nav, key headlines |
| `secondary` | Success, validated badges |
| `error` | Failures, destructive actions |
| `outline-variant` | Borders and dividers (preferred over `slate-200` in new pages) |
| `surface-*` | Page and card backgrounds |

Legacy mockups may still use `slate-*` classes; align them to tokens when touching those files.

---

## Layout patterns

### Bento grid

```html
<!-- Three columns -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <!-- cards -->
</div>

<!-- Mixed six-column -->
<div class="grid grid-cols-1 md:grid-cols-6 gap-6">
  <div class="md:col-span-4">Large card</div>
  <div class="md:col-span-2">Small card</div>
  <div class="md:col-span-2">Small card</div>
</div>
```

**Card gap:** always `gap-6` (24px).

### Main content wrapper

```html
<main class="ml-64 pt-24 pb-16 px-10 min-h-screen">
  <div class="max-w-[960px] mx-auto">
    <!-- page content -->
  </div>
</main>
```

### Example: new Settings page

Copy shell from `doc/mockup/data-import.html` (sidebar + top bar unchanged), then add page-specific content:

```html
<main class="ml-64 pt-24 pb-16 px-10 min-h-screen">
  <div class="max-w-[960px] mx-auto">
    <h1 class="font-headline-xl text-headline-xl mb-8">Settings</h1>
    <div class="space-y-6">
      <section class="p-6 rounded-xl bg-surface-container-lowest border border-outline-variant">
        <!-- form fields -->
      </section>
    </div>
  </div>
</main>
```

---

## Uniformity checklist

Use when adding or updating pages under `doc/mockup/`:

### Sidebar

- [ ] Home / History / enabled packages
- [ ] Active item: `border-primary`, primary-tinted background
- [ ] Footer: **Help** (`/help/`) then quieter **Open API** (`/docs`)

### Top bar

- [ ] Help link with `aria-label="User guide"` → `/help/` (or contextual `helpHref`)
- [ ] Open API primary button → `/docs`
- [ ] Height `h-16`
### Main content

- [ ] `ml-64 pt-24 pb-16 px-10`
- [ ] `max-w-[960px] mx-auto`
- [ ] Page title: `font-headline-xl`
- [ ] Cards: `rounded-xl`, `border-outline-variant`

### Typography and color

- [ ] Headlines: Manrope; body: Inter
- [ ] MD3 tokens over hardcoded grays where possible
- [ ] BIDS paths and metadata readable (mono for paths)

### Interaction

- [ ] Buttons: `active:scale-95` (or `active:scale-98` for icon-only)
- [ ] Hover: `opacity-90` or surface shift
- [ ] `transition-all duration-200` on interactive elements

---

## References

- [Material Design 3](https://m3.material.io/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Material Symbols](https://fonts.google.com/icons)
- [BIDS specification](https://bids.neuroimaging.io/)
- [NeuroFlow repository](https://github.com/acsenrafilho/neuroflow)

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-05-08 | Tim | Initial design system; sidebar/top bar; components |
| 2026-05-15 | — | English documentation; alignment with project standards; MD3 token examples; BIDS-oriented UX notes |
| 2026-06-01 | — | Simplified to one-page-per-tool modules; production reference `frontend/src/pages/tools/freesurfer.html`; removed pipeline configurator pattern |
| 2026-06-01 | — | Hub Package/Module table; batch upload; official docs button; job monitoring fields |
| 2026-06-01 | — | Wider hub (`max-w-[1400px]`); PNG logo; package pages; modules table filters and sort |
| 2026-07-25 | — | In-app Help wiki at `/help/`; sidebar Help vs Open API; NeuroFlow guide on tool/package pages |
| 2026-07-25 | — | Home Workspaces panel: create/list folders; Use + Open folder via `/api/v1/workspaces` |
| 2026-07-25 | — | Subject-centered datasets: outputs under `sub-<id>/derivatives/<package>/<module>/` |

**Last updated:** 2026-07-25
