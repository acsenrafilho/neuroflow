/**
 * Read-only ITK module page: documentation, host setup, and availability from the API.
 */
(function (global) {
  function statusBadge(available) {
    if (available) {
      return `<span class="inline-flex items-center gap-1 rounded-full bg-secondary/10 px-3 py-1 font-label-sm text-on-secondary-container"><span class="h-1.5 w-1.5 rounded-full bg-secondary"></span> Ready on this host</span>`;
    }
    return `<span class="inline-flex items-center gap-1 rounded-full bg-surface-container px-3 py-1 font-label-sm text-on-surface-variant"><span class="h-1.5 w-1.5 rounded-full bg-outline"></span> Install on host</span>`;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderHostSetup(config, available) {
    const lines = [];
    if (config.availabilityMode === "itk_binary") {
      lines.push(
        `<p>${escapeHtml(config.setupHint)}</p>`,
        `<p><strong>Config file:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">config/itk-binaries.json</code> (copy from <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">config/itk-binaries.example.json</code>).</p>`,
        `<p><strong>JSON key:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">${escapeHtml(config.configKey || "module_id")}</code></p>`,
        `<p><strong>Optional env:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">NEUROFLOW_ITK_BINARIES_CONFIG</code> to point at a custom JSON path.</p>`
      );
      if (!available) {
        lines.push(
          `<p class="text-on-surface">Status: binary not detected. After building on this machine, set an absolute executable path and restart the API or run host rescan.</p>`
        );
      }
    } else if (config.availabilityMode === "worker_package") {
      lines.push(`<p>${escapeHtml(config.setupHint)}</p>`);
      if (config.builtInSlicerModule) {
        lines.push(
          `<p><strong>In Slicer:</strong> open <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">${escapeHtml(config.slicerMenuPath || "Filtering → Simple Filters")}</code> from the module menu.</p>`,
          `<p><a href="/packages/slicer.html" class="font-semibold text-secondary hover:underline">3D Slicer package in NeuroFlow</a> — same host install and environment variables.</p>`
        );
      }
      lines.push(
        `<p><strong>Env:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">NEUROFLOW_SLICER_HOME</code> or <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">SLICER_HOME</code> (binary <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">Slicer</code> / <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">slicer</code>).</p>`
      );
      if (!available) {
        lines.push(
          `<p class="text-on-surface">Status: 3D Slicer was not found on this host. Install Slicer so Simple Filters is available in the desktop application.</p>`
        );
      }
    }
    return lines.join("");
  }

  function renderSimpleFiltersExtra(config) {
    const panels = (config.panels || [])
      .map(
        (panel) =>
          `<li class="space-y-1"><span class="font-medium text-on-surface">${escapeHtml(panel.name)}</span><span class="block text-on-surface-variant">${escapeHtml(panel.description)}</span></li>`
      )
      .join("");

    const notes = (config.notes || [])
      .map((note) => `<li>${escapeHtml(note)}</li>`)
      .join("");
    const tips = (config.tips || [])
      .map((tip) => `<li>${escapeHtml(tip)}</li>`)
      .join("");

    const imageBlock = config.docsImageUrl
      ? `<figure class="overflow-hidden rounded-lg border border-outline-variant/60">
          <img src="${escapeHtml(config.docsImageUrl)}" alt="Simple Filters module in 3D Slicer" class="w-full" loading="lazy" />
          <figcaption class="bg-surface-container-low px-4 py-2 text-xs text-on-surface-variant">Simple Filters UI (3D Slicer documentation)</figcaption>
        </figure>`
      : "";

    return `
      <section class="glass-panel flex flex-col gap-4 rounded-xl p-8 shadow-sm">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-secondary">info</span>
          <h2 class="font-headline-md text-on-surface">Overview</h2>
        </div>
        <p class="text-sm text-on-surface-variant">${escapeHtml(config.overview || "")}</p>
        ${imageBlock}
      </section>

      <section class="glass-panel flex flex-col gap-4 rounded-xl p-8 shadow-sm">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-secondary">tune</span>
          <h2 class="font-headline-md text-on-surface">Panels and workflow</h2>
        </div>
        <p class="text-sm text-on-surface-variant">
          In the Slicer application, use the module interface as documented below. NeuroFlow does not
          replicate this UI; batch jobs from the portal will be added in a later release.
        </p>
        <ol class="list-decimal space-y-4 pl-5 text-sm">${panels}</ol>
      </section>

      ${
        notes || tips
          ? `<section class="rounded-xl border border-outline-variant bg-surface-container-low px-6 py-5">
        <h2 class="mb-3 font-headline-md text-on-surface">Notes and tips</h2>
        ${notes ? `<div class="mb-3"><p class="mb-1 text-xs font-semibold uppercase tracking-wide text-on-surface-variant">Note</p><ul class="list-disc space-y-1 pl-5 text-sm text-on-surface-variant">${notes}</ul></div>` : ""}
        ${tips ? `<div><p class="mb-1 text-xs font-semibold uppercase tracking-wide text-on-surface-variant">Tip</p><ul class="list-disc space-y-1 pl-5 text-sm text-on-surface-variant">${tips}</ul></div>` : ""}
      </section>`
          : ""
      }`;
  }

  function configurePhaseBanner(moduleId, config, available) {
    const banner = document.getElementById("phase-banner");
    const titleEl = document.getElementById("phase-banner-title");
    const textEl = document.getElementById("phase-banner-text");
    const iconEl = document.getElementById("phase-banner-icon");
    if (!banner || !titleEl || !textEl) return;

    if (moduleId === "itk-simple-filter") {
      if (iconEl) iconEl.textContent = "desktop_windows";
      titleEl.textContent = "Use 3D Slicer on this host";
      if (available) {
        textEl.textContent =
          "Simple Filters is part of your 3D Slicer install. Open Slicer, go to Filtering → Simple Filters, pick a filter, set parameters, and click Apply. NeuroFlow job launch from the portal is not available yet.";
      } else {
        textEl.textContent =
          "Simple Filters ships with 3D Slicer. Install Slicer on this host (see Host setup below), then open Filtering → Simple Filters in the application. NeuroFlow job launch from the portal is not available yet.";
      }
      return;
    }

    if (iconEl) iconEl.textContent = "construction";
    titleEl.textContent = "Job launch coming soon";
    textEl.textContent =
      "This module page documents host setup and references. Upload, parameters, and job execution will be enabled in a future release once CLI details are finalized.";
  }

  async function init() {
    const params = new URLSearchParams(global.location.search);
    const moduleId = params.get("module");
    const config = moduleId && global.ITK_MODULES ? global.ITK_MODULES[moduleId] : null;

    const titleEl = document.getElementById("page-title");
    const summaryEl = document.getElementById("page-summary");
    const navLabel = document.getElementById("nav-module-label");
    const docsLink = document.getElementById("docs-link");
    const docsLabel = document.getElementById("docs-link-label");
    const statusEl = document.getElementById("host-status-badge");
    const setupEl = document.getElementById("host-setup-content");
    const workerPanel = document.getElementById("worker-panel");
    const workerSummary = document.getElementById("worker-summary");
    const extraEl = document.getElementById("module-extra-content");
    const hostSetupPanel = document.getElementById("host-setup-panel");

    if (!moduleId || !config) {
      if (titleEl) titleEl.textContent = "ITK module";
      if (summaryEl) {
        summaryEl.textContent =
          "Missing or unknown module. Open a module from the ITK package page or the Processing modules table.";
      }
      if (setupEl) {
        setupEl.innerHTML =
          '<p>Select a module via <code>?module=</code> in the URL, for example <code>itk-diffusion-complexity-mapping</code>.</p>';
      }
      return;
    }

    let apiModule = null;
    try {
      const modules = await global.NeuroflowApi.fetchJson("/api/v1/modules");
      apiModule = modules.find((m) => m.id === moduleId) || null;
    } catch {
      const fallback = global.NeuroflowApi.MODULES_FALLBACK || [];
      apiModule = fallback.find((m) => m.id === moduleId) || null;
    }

    const available = apiModule ? Boolean(apiModule.available) : false;
    const displayName = config.moduleName || apiModule?.module_name || moduleId;

    if (titleEl) titleEl.textContent = displayName;
    if (navLabel) navLabel.textContent = displayName;
    if (summaryEl) {
      summaryEl.textContent = config.summary || apiModule?.description || "";
    }
    if (docsLink && config.docsUrl) {
      docsLink.href = config.docsUrl;
    }
    if (docsLabel && config.docsLabel) {
      docsLabel.textContent = config.docsLabel;
    }
    if (statusEl) {
      statusEl.innerHTML = statusBadge(available);
      statusEl.classList.remove("hidden");
    }

    configurePhaseBanner(moduleId, config, available);

    if (moduleId === "itk-simple-filter" && extraEl) {
      extraEl.innerHTML = renderSimpleFiltersExtra(config);
      if (hostSetupPanel) {
        const hostTitle = hostSetupPanel.querySelector("h2");
        if (hostTitle) hostTitle.textContent = "Host setup (3D Slicer)";
      }
    } else if (extraEl) {
      extraEl.innerHTML = "";
    }

    if (setupEl) {
      setupEl.innerHTML = renderHostSetup(config, available);
    }

    if (config.availabilityMode === "worker_package" && workerPanel && workerSummary) {
      if (moduleId === "itk-simple-filter") {
        workerPanel.classList.remove("hidden");
        workerSummary.textContent =
          "Processing runs in the 3D Slicer desktop application. Simple Filters is a built-in module (Filtering category), not a separate download. Host readiness in NeuroFlow follows the same Slicer binary probe as the 3D Slicer package.";
      } else {
        workerPanel.classList.remove("hidden");
        workerSummary.textContent =
          "Jobs will run through 3D Slicer on the host. Host readiness follows the same Slicer discovery rules as the 3D Slicer package.";
      }
    } else if (workerPanel) {
      workerPanel.classList.add("hidden");
    }

    document.title = `NeuroFlow | ${displayName}`;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window);
