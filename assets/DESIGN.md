# 🎨 NeuroFlow Design System

Documentação dos padrões de design, componentes reutilizáveis e guidelines para manutenção uniforme do mockup NeuroFlow.

---

## 📋 Índice

1. [Design System MD3](#design-system-md3)
2. [Estrutura de Página](#estrutura-de-página)
3. [Componentes Reutilizáveis](#componentes-reutilizáveis)
4. [Tipografia](#tipografia)
5. [Cores & Tokens](#cores--tokens)
6. [Padrões de Layouts](#padrões-de-layouts)
7. [Checklist de Uniformidade](#checklist-de-uniformidade)

---

## 🎯 Design System MD3

NeuroFlow usa **Material Design 3 (MD3)** como sistema de design base com tokens de cor customizados.

### Aplicação em Uso

- **Framework CSS**: Tailwind CSS (via CDN)
- **Tipografia**: Inter (body) + Manrope (headlines)
- **Ícones**: Material Symbols Outlined (v24px)
- **Responsividade**: Mobile-first com breakpoint `md:` (768px+)

---

## 📐 Estrutura de Página

### Modelo Padrão (Todas as Páginas)

```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR (280px fixed)  |  TOP BAR (64px fixed)     │
│  ├─ Logo + Version      │  ├─ Search Box            │
│  ├─ Navigation Menu     │  ├─ Actions (notif, help) │
│  ├─ Run Pipeline Btn    │  └─ Export Button         │
│  ├─ Docs/Settings       │                           │
│  └─ Profile Info        │                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  MAIN CONTENT AREA (ml-64, pt-24)                  │
│  Max-width: 960px, centered                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Dimensões Padrão

```css
/* Sidebar */
width: 280px (w-64)
height: 100vh
position: fixed, left-0, top-0
padding: 24px (py-6)
border-right: 1px solid #e2e8f0

/* Top Bar */
height: 64px (h-16)
position: fixed, top-0, right-0, w-[calc(100%-16rem)]
padding: 32px (px-8)

/* Main Content */
margin-left: 64px (ml-64)
padding-top: 96px (pt-24)
max-width: 960px
padding: 40px (px-10)
```

---

## 🧩 Componentes Reutilizáveis

### 1. SIDEBAR (Fixo em Todas as Páginas)

```html
<aside class="fixed left-0 top-0 h-full w-64 border-r border-slate-200 bg-slate-50 flex flex-col py-6 z-50">
  <!-- Logo Section -->
  <div class="px-6 mb-8">
    <h1 class="text-lg font-bold tracking-tight text-blue-900">NeuroFlow</h1>
    <p class="text-xs text-slate-500">Clinical v2.4.0</p>
  </div>

  <!-- Navigation Menu -->
  <nav class="flex-1 space-y-1">
    <!-- Cada item segue padrão abaixo -->
  </nav>

  <!-- Run Pipeline Button -->
  <div class="px-4 mb-4">
    <button class="w-full bg-primary text-white py-2.5 rounded-lg font-label-sm flex items-center justify-center gap-2 hover:opacity-90 transition-all active:scale-95">
      <span class="material-symbols-outlined text-sm">play_arrow</span>
      Run Pipeline
    </button>
  </div>

  <!-- Footer Section (Docs, Settings, Profile) -->
  <div class="border-t border-slate-200 pt-4 space-y-1">
    <!-- Items aqui -->
  </div>
</aside>
```

#### Navigation Item - Padrão

**Inativo:**
```html
<a class="flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-100 hover:text-blue-700 cursor-pointer active:scale-95 transition-all duration-200" href="#">
  <span class="material-symbols-outlined">icon_name</span>
  <span class="font-label-sm">Label</span>
</a>
```

**Ativo:**
```html
<a class="flex items-center gap-3 px-4 py-3 border-l-4 border-primary bg-blue-50 text-blue-800 font-semibold cursor-pointer active:scale-95 transition-all duration-200" href="#">
  <span class="material-symbols-outlined">icon_name</span>
  <span class="font-label-sm">Label</span>
</a>
```

**Diferenças:**
- Ativo: `border-l-4 border-primary` (sempre usar `primary`, nunca outra cor)
- Ativo: `bg-blue-50` (cor de background sempre igual)
- Ativo: `text-blue-800 font-semibold` (destaque visual)

#### Profile Section - Padrão

```html
<div class="px-4 py-3 flex items-center gap-3 mt-2">
  <img alt="Clinician Profile" class="w-8 h-8 rounded-full border border-slate-200" src="[URL]"/>
  <div class="overflow-hidden">
    <p class="text-xs font-semibold text-slate-900 truncate">Dr. Aris Thorne</p>
    <p class="text-[10px] text-slate-500">Neuro-Radiology</p>
  </div>
</div>
```

---

### 2. TOP BAR (Fixo em Todas as Páginas)

```html
<header class="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 bg-white/80 backdrop-blur-md z-40 flex justify-between items-center px-8 border-b border-slate-200 shadow-sm">
  <!-- Search Box (Left Side) -->
  <div class="flex items-center gap-4 flex-1">
    <div class="relative w-full max-w-md">
      <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">search</span>
      <input class="w-full bg-slate-50 border-slate-200 rounded-full pl-10 pr-4 py-1.5 text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all" placeholder="Placeholder médico aqui..." type="text"/>
    </div>
  </div>

  <!-- Actions & Export (Right Side) -->
  <div class="flex items-center gap-6">
    <!-- Notifications & Help -->
    <div class="flex items-center gap-4 text-slate-500">
      <button class="hover:text-primary transition-colors active:scale-98">
        <span class="material-symbols-outlined">notifications_active</span>
      </button>
      <button class="hover:text-primary transition-colors active:scale-98">
        <span class="material-symbols-outlined">help_outline</span>
      </button>
    </div>

    <!-- Divider -->
    <div class="h-6 w-px bg-slate-200"></div>

    <!-- Export Button (PRIMARY FILLED - PADRÃO) -->
    <button class="bg-primary text-white px-4 py-1.5 rounded-lg text-sm font-semibold hover:opacity-90 transition-all active:scale-95">
      Export
    </button>
  </div>
</header>
```

---

### 3. Card - Padrão Bento Style

```html
<!-- Card Normal -->
<div class="p-6 rounded-xl bg-surface-container-lowest border border-slate-200 shadow-[0px_4px_12px_rgba(13,92,150,0.08)] flex flex-col group transition-all hover:border-primary-container">
  <!-- Icon + Checkbox -->
  <div class="flex justify-between items-start mb-4">
    <div class="p-2 bg-primary-fixed rounded-lg text-primary">
      <span class="material-symbols-outlined text-2xl">icon_name</span>
    </div>
    <input class="w-5 h-5 rounded border-slate-300 text-secondary focus:ring-secondary" type="checkbox"/>
  </div>

  <!-- Content -->
  <h3 class="font-headline-md text-headline-md mb-1 text-lg">Title</h3>
  <p class="font-label-sm text-label-sm text-on-surface-variant mb-4">Description</p>

  <!-- Badges -->
  <div class="mt-auto">
    <span class="px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container text-[12px] font-bold">✓ Validado</span>
  </div>
</div>
```

**Aplicação:**
- Badges sempre `rounded-full` com `px-2 py-0.5`
- Status badge: use cores MD3 (primary-fixed, secondary-container, etc)
- Hover effect: `hover:border-primary-container` (sempre)

---

### 4. Button - Padrões

```html
<!-- Primary Filled (CTA Principal) -->
<button class="bg-primary text-white px-4 py-2 rounded-lg font-semibold hover:opacity-90 transition-all active:scale-95">
  Action
</button>

<!-- Secondary (Alternativa) -->
<button class="bg-secondary text-white px-4 py-2 rounded-lg font-semibold hover:opacity-90 transition-all active:scale-95">
  Action
</button>

<!-- Tertiary (Low Priority) -->
<button class="border border-slate-300 text-slate-600 px-4 py-2 rounded-lg font-semibold hover:bg-slate-50 transition-all active:scale-95">
  Action
</button>
```

---

## 🔤 Tipografia

### Hierarquia de Fontes

| Elemento | Fonte | Peso | Tamanho | Uso |
|----------|-------|------|--------|-----|
| Headlines Xtra-Large | Manrope | 700 | 40px | Page titles |
| Headlines Large | Manrope | 600 | 32px | Section titles |
| Headlines Medium | Manrope | 600 | 24px | Subsections |
| Body Large | Inter | 400 | 18px | Long-form text |
| Body Medium | Inter | 400 | 16px | Main body text |
| Label Small | Inter | 500 | 14px | Button labels, nav |
| Code Mono | Monospace | 400 | 14px | Code snippets |

### Aplicação em Tailwind

```html
<!-- Headline XL -->
<h1 class="font-headline-xl text-headline-xl">Title</h1>

<!-- Headline MD -->
<h3 class="font-headline-md text-headline-md">Subtitle</h3>

<!-- Body MD -->
<p class="font-body-md text-body-md">Text</p>

<!-- Label SM -->
<span class="font-label-sm text-label-sm">Label</span>
```

---

## 🎨 Cores & Tokens

### Paleta Completa MD3

```javascript
{
  primary: "#004473",                    // Azul principal (CTAs)
  primary-container: "#0d5c96",         // Fundo primary light
  primary-fixed: "#d0e4ff",             // Fixed variant light
  primary-fixed-dim: "#9ccaff",         // Fixed variant dim
  
  secondary: "#006c46",                 // Verde (success, alternativa)
  secondary-container: "#6af9b5",       // Fundo secondary light
  secondary-fixed: "#6dfcb8",           // Fixed variant
  
  tertiary: "#004664",                  // Terceira cor
  tertiary-container: "#005f85",        // Fundo tertiary
  tertiary-fixed: "#c6e7ff",            // Fixed variant
  
  surface: "#f7f9fb",                   // Background principal
  surface-container-low: "#f2f4f6",     // Fundo mais claro
  surface-container: "#eceef0",         // Fundo médio
  surface-container-high: "#e6e8ea",    // Fundo mais escuro
  
  outline: "#717781",                   // Borders padrão
  outline-variant: "#c1c7d1",          // Borders light
  
  error: "#ba1a1a",                     // Erro/destruição
  error-container: "#ffdad6",           // Fundo erro
  
  on-surface: "#191c1e",                // Texto sobre surface
  on-surface-variant: "#414750",        // Texto secondary
}
```

### Regras de Uso

- **Primary (#004473)**: CTAs, Headlines, Active states
- **Secondary (#006c46)**: Success states, badges ✓
- **Error (#ba1a1a)**: Warnings, destructive actions
- **Surface tokens**: Sempre usar `outline-variant` para borders (nunca hardcode `slate-200`)

---

## 📐 Padrões de Layouts

### 1. Bento Grid (Variável por página)

```html
<!-- 3-column layout -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <!-- Cards aqui -->
</div>

<!-- 6-column mixed layout -->
<div class="grid grid-cols-1 md:grid-cols-6 gap-6">
  <div class="md:col-span-4">Large card</div>
  <div class="md:col-span-2">Small card</div>
  <div class="md:col-span-2">Small card</div>
</div>
```

**Espaçamento entre cards**: SEMPRE `gap-6` (24px)

### 2. Content Container

```html
<!-- Padrão para main content -->
<main class="ml-64 pt-24 pb-16 px-10 min-h-screen">
  <div class="max-w-[960px] mx-auto">
    <!-- Content aqui -->
  </div>
</main>
```

---

## ✅ Checklist de Uniformidade

Use este checklist ao adicionar NOVAS páginas:

### Sidebar ✓
- [ ] Logo "NeuroFlow" + "Clinical v2.4.0"
- [ ] Navegação com `space-y-1`
- [ ] Active state: `border-primary` (sempre azul)
- [ ] Active state background: `bg-blue-50`
- [ ] "Run Pipeline" button em `mt-auto` com `px-4 mb-4`
- [ ] Docs/Settings footer section
- [ ] Profile section com img + name + specialty

### Top Bar ✓
- [ ] Search box: max-w-md, rounded-full
- [ ] Notifications + Help buttons
- [ ] Export button: `bg-primary text-white`
- [ ] Height: 64px (h-16)
- [ ] Divider between actions and export

### Main Content ✓
- [ ] `ml-64 pt-24 pb-16 px-10`
- [ ] `max-w-[960px] mx-auto`
- [ ] Page title: `font-headline-xl`
- [ ] Subtitle: `font-headline-md`
- [ ] Cards: `rounded-xl`, `border-outline-variant`, consistent shadows

### Typography ✓
- [ ] Headlines sempre Manrope
- [ ] Body sempre Inter
- [ ] Tamanhos consistent com tabela acima
- [ ] Font weights correct

### Colors ✓
- [ ] Use tokens MD3, não hardcode cores
- [ ] Borders: `border-outline-variant` (nunca `slate-200`)
- [ ] Active states: `primary` color
- [ ] Badges: MD3 container colors

### Interactions ✓
- [ ] Buttons: `active:scale-95` ou `active:scale-98`
- [ ] Hover effects: `opacity-90` ou background color change
- [ ] Transitions: `transition-all duration-200`

---

## 📝 Exemplo: Nova Página (Settings)

```html
<!-- Copiar structure de data-import.html -->
<!-- 1. Sidebar (IDÊNTICO) -->
<!-- 2. Top Bar (IDÊNTICO) -->
<!-- 3. Main content unique para Settings -->

<main class="ml-64 pt-24 pb-16 px-10 min-h-screen">
  <div class="max-w-[960px] mx-auto">
    <!-- Page specific content -->
    <h1 class="font-headline-xl text-headline-xl mb-8">Settings</h1>
    
    <!-- Form sections com cards -->
    <div class="space-y-6">
      <div class="p-6 rounded-xl bg-surface-container-lowest border border-outline-variant">
        <!-- Content aqui, seguindo padrões acima -->
      </div>
    </div>
  </div>
</main>
```

---

## 🔗 Referências

- **Material Design 3**: https://m3.material.io/
- **Tailwind CSS**: https://tailwindcss.com/
- **Material Symbols**: https://fonts.google.com/icons
- **GitHub NeuroFlow**: [insira URL]

---

## 📋 Histórico de Mudanças

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-08 | Tim | Criação inicial do design system |
| | | Padronização sidebar/top-bar |
| | | Documentação componentes |

---

**Última atualização**: 2026-05-08  
**Status**: ✅ FINAL - Ready for Review
