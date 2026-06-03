/**
 * Shared sidebar and top bar for hub and package pages.
 */
(function (global) {
  const PACKAGES = [
    { id: "freesurfer", name: "FreeSurfer", icon: "neurology", href: "/packages/freesurfer.html", enabled: true },
    { id: "fsl", name: "FSL", icon: "science", href: "/packages/fsl.html", enabled: true },
    { id: "ants", name: "ANTs", icon: "transform", href: "/packages/ants.html", enabled: true },
    { id: "slicer", name: "3D Slicer", icon: "view_in_ar", href: "/packages/slicer.html", enabled: true },
  ];

  const LOGO_SRC = "/assets/neuroflow_logo.png";

  function navItem({ href, icon, label, active, disabled }) {
    if (disabled) {
      return `
        <span class="flex cursor-not-allowed items-center gap-3 border-l-4 border-transparent px-4 py-3 text-on-surface-variant/50" aria-disabled="true">
          <span class="material-symbols-outlined">${icon}</span>
          <span class="font-label-sm">${label}</span>
        </span>`;
    }
    const activeClass = active
      ? "border-primary bg-primary/10 font-semibold text-primary"
      : "border-transparent text-on-surface-variant hover:bg-surface-container";
    const iconClass = active ? "text-primary" : "";
    return `
      <a href="${href}" class="flex items-center gap-3 border-l-4 ${activeClass} px-4 py-3 transition-all">
        <span class="material-symbols-outlined ${iconClass}">${icon}</span>
        <span class="font-label-sm">${label}</span>
      </a>`;
  }

  function renderSidebar(options) {
    const active = options?.active || "home";
    const el = document.getElementById("hub-sidebar");
    if (!el) return;

    const packageNav = PACKAGES.map((pkg) =>
      navItem({
        href: pkg.href,
        icon: pkg.icon,
        label: pkg.name,
        active: active === pkg.id,
        disabled: !pkg.enabled,
      })
    ).join("");

    el.innerHTML = `
      <div class="mb-8 px-6">
        <p class="mt-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Facilitation portal
        </p>
      </div>
      <nav class="flex-1 space-y-1 px-2" aria-label="Main navigation">
        ${navItem({ href: "/", icon: "home", label: "Home", active: active === "home" })}
        ${packageNav}
      </nav>
      <div class="space-y-1 border-t border-outline-variant px-2 pt-4">
        <a href="/docs" class="flex items-center gap-3 px-4 py-3 text-on-surface-variant transition-all hover:bg-surface-container hover:text-primary">
          <span class="material-symbols-outlined">menu_book</span>
          <span class="font-label-sm">API documentation</span>
        </a>
      </div>`;
    el.className =
      "fixed left-0 top-0 z-50 flex h-full w-64 flex-col border-r border-outline-variant bg-surface-container-low py-6";
    el.setAttribute("aria-label", "Main navigation");
  }

  function renderHeader(options) {
    const title = options?.title || "Home";
    const showApi = options?.showApi !== false;
    const el = document.getElementById("hub-header");
    if (!el) return;

    el.innerHTML = `
      <h1 class="font-headline-md text-on-surface">${title}</h1>
      <div class="flex items-center gap-6">
        <button type="button" class="text-on-surface-variant transition-colors hover:text-primary" title="Help">
          <span class="material-symbols-outlined">help_outline</span>
        </button>
        ${
          showApi
            ? `
        <div class="h-6 w-px bg-outline-variant"></div>
        <a href="/docs" class="rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-on-primary transition-all hover:opacity-90 active:scale-95">
          Open API
        </a>`
            : ""
        }
      </div>`;
    el.className =
      "fixed right-0 top-0 z-40 flex h-16 w-[calc(100%-16rem)] items-center justify-between border-b border-outline-variant bg-surface-container-lowest/90 px-8 shadow-sm backdrop-blur-md";
  }

  function init(options) {
    renderSidebar(options);
    renderHeader(options);
  }

  global.HubLayout = { PACKAGES, LOGO_SRC, init, renderSidebar, renderHeader };
})(window);
