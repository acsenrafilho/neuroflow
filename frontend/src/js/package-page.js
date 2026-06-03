/**
 * Package overview page: lists all modules for window.PACKAGE_ID.
 */
(function (global) {
  const PACKAGE_META = {
    freesurfer: {
      docsUrl: "https://surfer.nmr.mgh.harvard.edu/",
      docsLabel: "FreeSurfer project site",
    },
    fsl: {
      docsUrl: "https://fsl.fmrib.ox.ac.uk/fsl/docs/index.html",
      docsLabel: "FSL documentation",
    },
    ants: {
      docsUrl: "https://github.com/ANTsX/ANTs/wiki",
      docsLabel: "ANTs wiki",
    },
    itk: {
      docsUrl: "https://github.com/CSIM-Toolkits/ITK/tree/master",
      docsLabel: "CSIM ITK repository",
    },
  };

  function statusLabel(module) {
    if (module.coming_soon && !module.available) return "Coming soon";
    if (module.available) return "Ready";
    return "Install on host";
  }

  function statusBadge(module) {
    const label = statusLabel(module);
    if (module.coming_soon && !module.available) {
      return `<span class="rounded-full bg-surface-container px-3 py-1 font-label-sm text-on-surface-variant">${label}</span>`;
    }
    if (module.available) {
      return `<span class="inline-flex items-center gap-1 rounded-full bg-secondary/10 px-3 py-1 font-label-sm text-on-secondary-container"><span class="h-1.5 w-1.5 rounded-full bg-secondary"></span> ${label}</span>`;
    }
    return `<span class="inline-flex items-center gap-1 rounded-full bg-surface-container px-3 py-1 font-label-sm text-on-surface-variant"><span class="h-1.5 w-1.5 rounded-full bg-outline"></span> ${label}</span>`;
  }

  function renderModuleRow(module) {
    const moduleUrl = module.coming_soon
      ? null
      : `${module.page_path}?module=${encodeURIComponent(module.id)}`;
    const action = moduleUrl
      ? `<a href="${moduleUrl}" class="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 font-semibold text-on-primary transition-all hover:opacity-90"><span class="material-symbols-outlined text-sm">open_in_new</span> Open module</a>`
      : `<span class="text-on-surface-variant">—</span>`;

    return `
      <tr class="${module.coming_soon ? "opacity-70" : "hover:bg-surface-container-low/50"}">
        <td class="px-6 py-4 font-medium text-on-surface">${module.module_name}</td>
        <td class="px-6 py-4 text-on-surface-variant">${module.description}</td>
        <td class="px-6 py-4">${statusBadge(module)}</td>
        <td class="px-6 py-4">${action}</td>
      </tr>`;
  }

  async function init() {
    const packageId = global.PACKAGE_ID;
    if (!packageId) return;

    const titleEl = document.getElementById("package-title");
    const summaryEl = document.getElementById("package-summary");
    const docsEl = document.getElementById("package-docs");
    const tbody = document.getElementById("package-modules-body");
    const countEl = document.getElementById("package-modules-count");
    const bannerEl = document.getElementById("package-coming-soon-banner");

    let modules;
    let offline = false;
    try {
      modules = await NeuroflowApi.fetchJson("/api/v1/modules");
    } catch {
      modules = NeuroflowApi.MODULES_FALLBACK;
      offline = true;
    }

    const packageModules = modules.filter((m) => m.package_id === packageId);
    const packageName = packageModules[0]?.package_name || packageId;
    const allComingSoon = packageModules.every((m) => m.coming_soon);

    HubLayout.init({ active: packageId, title: packageName, showApi: true });

    if (titleEl) titleEl.textContent = packageName;
    if (summaryEl) {
      if (allComingSoon) {
        summaryEl.textContent = `${packageName} integration is planned for a future release.`;
      } else if (packageId === "freesurfer") {
        summaryEl.textContent =
          "Cortical reconstruction and volumetric segmentation. Choose a pipeline module below.";
      } else if (packageId === "fsl") {
        summaryEl.textContent =
          "Structural, diffusion, and registration tools. Complete prerequisite steps in linked modules before advanced pipelines.";
      } else if (packageId === "itk") {
        summaryEl.textContent =
          "CSIM ITK filters built on the host plus Simple Filters via 3D Slicer. Configure native binaries in config/itk-binaries.json.";
      } else {
        summaryEl.textContent = `Processing modules available under ${packageName}.`;
      }
    }

    const meta = PACKAGE_META[packageId];
    if (docsEl && meta?.docsUrl) {
      docsEl.innerHTML = `
        <a href="${meta.docsUrl}" target="_blank" rel="noopener noreferrer"
          class="inline-flex items-center gap-2 rounded-lg border border-secondary bg-surface-container-lowest px-4 py-2 font-label-sm text-secondary transition-colors hover:bg-secondary/10">
          <span class="material-symbols-outlined text-sm">open_in_new</span>
          ${meta.docsLabel}
        </a>`;
      docsEl.classList.remove("hidden");
    }

    if (bannerEl && allComingSoon) {
      bannerEl.classList.remove("hidden");
    }

    const ready = packageModules.filter((m) => m.available && !m.coming_soon).length;
    if (countEl) {
      countEl.textContent = offline
        ? `${packageModules.length} module(s) — offline catalog`
        : `${ready} of ${packageModules.length} module(s) ready on this host`;
    }

    if (tbody) {
      if (packageModules.length === 0) {
        tbody.innerHTML = `
          <tr><td colspan="4" class="px-6 py-8 text-center text-on-surface-variant">No modules listed for this package.</td></tr>`;
      } else {
        tbody.innerHTML = packageModules
          .sort((a, b) => a.module_name.localeCompare(b.module_name))
          .map(renderModuleRow)
          .join("");
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
