/**
 * ITK tool page: runnable modules (CLI jobs) or read-only docs (e.g. Simple Filters).
 */
(function (global) {
  const modules = global.ITK_MODULES || {};

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

  function renderReadOnlyHostSetup(config, available) {
    const lines = [];
    if (config.availabilityMode === "itk_binary") {
      lines.push(
        `<p>${escapeHtml(config.setupHint)}</p>`,
        `<p><strong>Config file:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">config/itk-binaries.json</code></p>`,
        `<p><strong>JSON key:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">${escapeHtml(config.configKey || "module_id")}</code></p>`
      );
      if (!available) {
        lines.push(
          `<p class="text-on-surface">Status: binary not detected. Configure an absolute executable path and rescan the host.</p>`
        );
      }
    } else if (config.availabilityMode === "worker_package") {
      lines.push(`<p>${escapeHtml(config.setupHint)}</p>`);
      if (config.builtInSlicerModule) {
        lines.push(
          `<p><strong>In Slicer:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">${escapeHtml(config.slicerMenuPath || "Filtering → Simple Filters")}</code></p>`,
          `<p><a href="/packages/slicer.html" class="font-semibold text-secondary hover:underline">3D Slicer package in NeuroFlow</a></p>`
        );
      }
      lines.push(
        `<p><strong>Env:</strong> <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">NEUROFLOW_SLICER_HOME</code> or <code class="rounded bg-surface-container px-1.5 py-0.5 text-on-surface">SLICER_HOME</code></p>`
      );
      if (!available) {
        lines.push(`<p class="text-on-surface">Status: 3D Slicer was not found on this host.</p>`);
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
    const notes = (config.notes || []).map((note) => `<li>${escapeHtml(note)}</li>`).join("");
    const tips = (config.tips || []).map((tip) => `<li>${escapeHtml(tip)}</li>`).join("");
    const imageBlock = config.docsImageUrl
      ? `<figure class="overflow-hidden rounded-lg border border-outline-variant/60">
          <img src="${escapeHtml(config.docsImageUrl)}" alt="Simple Filters in 3D Slicer" class="w-full" loading="lazy" />
        </figure>`
      : "";
    return `
      <section class="glass-panel flex flex-col gap-4 rounded-xl p-8 shadow-sm">
        <h2 class="font-headline-md text-on-surface">Overview</h2>
        <p class="text-sm text-on-surface-variant">${escapeHtml(config.overview || "")}</p>
        ${imageBlock}
      </section>
      <section class="glass-panel flex flex-col gap-4 rounded-xl p-8 shadow-sm">
        <h2 class="font-headline-md text-on-surface">Panels and workflow</h2>
        <ol class="list-decimal space-y-4 pl-5 text-sm">${panels}</ol>
      </section>
      ${
        notes || tips
          ? `<section class="rounded-xl border border-outline-variant bg-surface-container-low px-6 py-5">
        <h2 class="mb-3 font-headline-md text-on-surface">Notes and tips</h2>
        ${notes ? `<ul class="list-disc space-y-1 pl-5 text-sm text-on-surface-variant">${notes}</ul>` : ""}
        ${tips ? `<ul class="mt-3 list-disc space-y-1 pl-5 text-sm text-on-surface-variant">${tips}</ul>` : ""}
      </section>`
          : ""
      }`;
  }

  async function initReadOnly(moduleId, config) {
    const readOnlySections = document.getElementById("read-only-sections");
    readOnlySections?.classList.remove("hidden");
    document.getElementById("job-form")?.classList.add("hidden");

    let apiModule = null;
    try {
      const list = await global.NeuroflowApi.fetchJson("/api/v1/modules");
      apiModule = list.find((m) => m.id === moduleId) || null;
    } catch {
      apiModule = (global.NeuroflowApi.MODULES_FALLBACK || []).find((m) => m.id === moduleId) || null;
    }
    const available = apiModule ? Boolean(apiModule.available) : false;
    const displayName = config.moduleName || moduleId;

    document.getElementById("page-title").textContent = displayName;
    document.getElementById("page-summary").textContent = config.summary || "";
    document.getElementById("nav-module-label").textContent = displayName;
    const docsLink = document.getElementById("docs-link");
    const docsLabel = document.getElementById("docs-link-label");
    if (docsLink && config.docsUrl) docsLink.href = config.docsUrl;
    if (docsLabel && config.docsLabel) docsLabel.textContent = config.docsLabel;
    const statusEl = document.getElementById("host-status-badge");
    if (statusEl) {
      statusEl.innerHTML = statusBadge(available);
      statusEl.classList.remove("hidden");
    }

    const phaseIcon = document.getElementById("phase-banner-icon");
    const phaseTitle = document.getElementById("phase-banner-title");
    const phaseText = document.getElementById("phase-banner-text");
    if (moduleId === "itk-simple-filter") {
      if (phaseIcon) phaseIcon.textContent = "desktop_windows";
      if (phaseTitle) phaseTitle.textContent = "Use 3D Slicer on this host";
      if (phaseText) {
        phaseText.textContent = available
          ? "Open Slicer → Filtering → Simple Filters. Portal batch jobs are not available yet."
          : "Install 3D Slicer on this host, then open Filtering → Simple Filters in the application.";
      }
      const extra = document.getElementById("module-extra-content");
      if (extra) extra.innerHTML = renderSimpleFiltersExtra(config);
    } else if (phaseText) {
      phaseText.textContent =
        "This module is documented here; job launch from NeuroFlow is not enabled yet.";
    }

    const setupEl = document.getElementById("host-setup-content");
    if (setupEl) setupEl.innerHTML = renderReadOnlyHostSetup(config, available);

    const workerPanel = document.getElementById("worker-panel");
    const workerSummary = document.getElementById("worker-summary");
    if (moduleId === "itk-simple-filter" && workerPanel && workerSummary) {
      workerPanel.classList.remove("hidden");
      workerSummary.textContent =
        "Simple Filters is built into 3D Slicer. Host readiness uses the same Slicer binary probe as the 3D Slicer package.";
    }

    document.title = `NeuroFlow | ${displayName}`;
  }

  const form = document.getElementById("job-form");
  const runBtn = document.getElementById("run-btn");
  const statusPanel = document.getElementById("status-panel");
  const logOutput = document.getElementById("log-output");
  const progressBar = document.getElementById("progress-bar");
  const formError = document.getElementById("form-error");
  const prerequisitesEl = document.getElementById("prerequisites-panel");
  const prerequisitesList = document.getElementById("prerequisites-list");
  const inputsSection = document.getElementById("inputs-section");
  const paramsSection = document.getElementById("params-section");
  const paramsGrid = document.getElementById("params-grid");
  const cliPreview = document.getElementById("cli-preview");
  const outputPrefixInput = document.getElementById("output_prefix");
  const timeEstimateEl = document.getElementById("time-estimate");

  const queryModuleId = new URLSearchParams(global.location.search).get("module");
  let activeConfig = null;
  let activeModuleId = queryModuleId || "itk-diffusion-complexity-mapping";
  let hoursPerScan = 0.1;
  let pollTimer = null;
  let currentJobId = null;
  const TOOL_ID = "itk";

  /** @type {Map<string, File[]>} */
  const filesByRole = new Map();

  function formatDuration(seconds) {
    if (seconds == null || seconds < 0) return "—";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
  }

  function formatHours(h) {
    if (h < 1) return `~${Math.round(h * 60)} min`;
    return `~${h}h`;
  }

  function modulePageUrl(moduleId) {
    return `/tools/itk.html?module=${encodeURIComponent(moduleId)}`;
  }

  function allowsMultiple(inputDef) {
    if (inputDef.multiple) return true;
    if (activeConfig?.batchDriverRole === inputDef.role) return true;
    if (activeConfig?.batchDriverRole == null && inputDef.required) return true;
    return false;
  }

  function batchRunCount() {
    if (!activeConfig) return 0;
    const driver = activeConfig.batchDriverRole;
    if (driver) {
      return (filesByRole.get(driver) || []).length;
    }
    const required = activeConfig.inputs.filter((i) => i.required);
    const counts = required.map((i) => (filesByRole.get(i.role) || []).length);
    if (counts.some((c) => c === 0)) return 0;
    const unique = new Set(counts);
    return unique.size === 1 ? counts[0] : 0;
  }

  function renderPrerequisites(config) {
    if (!config.prerequisites || config.prerequisites.length === 0) {
      prerequisitesEl.classList.add("hidden");
      return;
    }
    prerequisitesEl.classList.remove("hidden");
    prerequisitesList.innerHTML = config.prerequisites
      .map((step, index) => {
        const link =
          step.moduleId != null
            ? `<a href="${modulePageUrl(step.moduleId)}" class="font-semibold text-secondary hover:underline">${step.moduleId.replace("itk-", "").toUpperCase()} module</a>`
            : "";
        const suffix = step.moduleId ? ` — open the ${link}` : "";
        return `<li><span class="font-semibold text-on-surface">${index + 1}.</span> ${step.text}${suffix}</li>`;
      })
      .join("");
  }

  function renderFileList(role, container) {
    const list = filesByRole.get(role) || [];
    if (list.length === 0) {
      container.textContent = "No file selected";
      container.className = "text-xs text-on-surface-variant";
      return;
    }
    container.className = "text-xs text-on-surface";
    container.innerHTML = list
      .map(
        (f, idx) =>
          `<div class="flex items-center justify-between gap-2 py-1">
            <span class="truncate">${f.name}</span>
            <button type="button" class="remove-batch-file text-on-surface-variant hover:text-error" data-role="${role}" data-index="${idx}" title="Remove">
              <span class="material-symbols-outlined text-sm">close</span>
            </button>
          </div>`
      )
      .join("");
    container.querySelectorAll(".remove-batch-file").forEach((btn) => {
      btn.addEventListener("click", () => {
        const r = btn.dataset.role;
        const idx = Number(btn.dataset.index);
        const arr = [...(filesByRole.get(r) || [])];
        arr.splice(idx, 1);
        if (arr.length) filesByRole.set(r, arr);
        else filesByRole.delete(r);
        renderFileList(r, container);
        updateCliPreview();
        updateTimeEstimate();
      });
    });
  }

  function renderInputs(config) {
    inputsSection.innerHTML = "";
    filesByRole.clear();

    const batchHint = document.createElement("p");
    batchHint.className = "text-sm text-on-surface-variant";
    if (config.batchDriverRole) {
      batchHint.textContent =
        "Select multiple files on the primary input to run the same command sequentially (one job per file). Sidecar files are shared across runs unless you upload one per run.";
    } else {
      batchHint.textContent =
        "For paired inputs (e.g. moving + reference), select the same number of files in each required field to queue sequential runs.";
    }
    inputsSection.appendChild(batchHint);

    config.inputs.forEach((inputDef) => {
      const multi = allowsMultiple(inputDef);
      const block = document.createElement("div");
      block.className = "flex flex-col gap-2 rounded-lg border border-outline-variant/50 p-4";
      const requiredMark = inputDef.required ? " *" : "";
      block.innerHTML = `
        <label class="font-label-sm text-on-surface">${inputDef.label}${requiredMark}</label>
        <input
          type="file"
          class="itk-file-input rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-2 text-sm"
          data-role="${inputDef.role}"
          accept="${inputDef.accept || ".nii,.nii.gz,.gz"}"
          ${multi ? "multiple" : ""}
        />
        <div class="file-list" data-filename="${inputDef.role}"></div>
      `;
      inputsSection.appendChild(block);

      const fileInput = block.querySelector(".itk-file-input");
      const listEl = block.querySelector(`[data-filename="${inputDef.role}"]`);

      fileInput.addEventListener("change", () => {
        const picked = Array.from(fileInput.files || []);
        if (!picked.length) {
          filesByRole.delete(inputDef.role);
        } else if (multi) {
          const existing = filesByRole.get(inputDef.role) || [];
          const merged = [...existing];
          for (const file of picked) {
            if (
              !merged.some((f) => f.name === file.name && f.size === file.size && f.lastModified === file.lastModified)
            ) {
              merged.push(file);
            }
          }
          filesByRole.set(inputDef.role, merged);
        } else {
          filesByRole.set(inputDef.role, [picked[0]]);
        }
        // Clear picker so the same files can be added again; validation uses filesByRole, not the input.
        fileInput.value = "";
        renderFileList(inputDef.role, listEl);
        updateCliPreview();
        updateTimeEstimate();
      });
    });
  }

  function collectParameters() {
    const params = {};
    if (!activeConfig) return params;
    for (const def of activeConfig.params || []) {
      const el = document.getElementById(`param-${def.name}`);
      if (!el) continue;
      if (def.type === "checkbox") {
        params[def.name] = el.checked;
      } else if (def.type === "number") {
        const val = el.value.trim();
        if (val !== "") params[def.name] = Number(val);
      } else if (el.value.trim() !== "") {
        params[def.name] = el.value.trim();
      }
    }
    return params;
  }

  function renderParams(config) {
    paramsGrid.innerHTML = "";
    if (!config.params || config.params.length === 0) {
      paramsSection.classList.add("hidden");
      return;
    }
    paramsSection.classList.remove("hidden");

    config.params.forEach((def) => {
      const wrap = document.createElement("div");
      wrap.className = "flex flex-col gap-2";

      if (def.type === "checkbox") {
        wrap.innerHTML = `
          <label class="flex items-center gap-2 font-label-sm text-on-surface">
            <input type="checkbox" id="param-${def.name}" class="rounded border-outline-variant" ${def.default ? "checked" : ""} />
            ${def.label}
          </label>`;
      } else if (def.type === "select") {
        const options = (def.options || [])
          .map(
            (o) =>
              `<option value="${o.value}" ${o.value === def.default ? "selected" : ""}>${o.label}</option>`
          )
          .join("");
        wrap.innerHTML = `
          <label class="font-label-sm text-on-surface" for="param-${def.name}">${def.label}</label>
          <select id="param-${def.name}" class="rounded-lg border-outline-variant bg-surface-container-lowest font-body-md">${options}</select>`;
      } else {
        const step = def.step != null ? `step="${def.step}"` : "";
        const min = def.min != null ? `min="${def.min}"` : "";
        const max = def.max != null ? `max="${def.max}"` : "";
        wrap.innerHTML = `
          <label class="font-label-sm text-on-surface" for="param-${def.name}">${def.label}</label>
          <input type="${def.type || "text"}" id="param-${def.name}" class="rounded-lg border-outline-variant bg-surface-container-lowest font-body-md"
            value="${def.default ?? ""}" ${step} ${min} ${max} />`;
      }
      paramsGrid.appendChild(wrap);
      wrap.querySelectorAll("input, select").forEach((el) => {
        el.addEventListener("input", updateCliPreview);
        el.addEventListener("change", updateCliPreview);
      });
    });
  }

  function updateCliPreview() {
    if (!activeConfig) return;
    const prefix = outputPrefixInput?.value.trim() || "result";
    const params = collectParameters();
    const n = batchRunCount();
    const inputName = (filesByRole.get("input") || [])[0]?.name || "<inputImage>";
    const maskFiles = filesByRole.get("mask") || [];
    const maskName = maskFiles[0]?.name;
    const useMask = Boolean(params.use_mask) && maskFiles.length > 0;
    const q = params.q_value != null ? params.q_value : 1;
    const outName = `${prefix}.nii.gz`;
    let cmd = `DiffusionComplexityMapping ${inputName}`;
    if (useMask && maskName) {
      cmd += ` ${maskName} ${outName} ${q}`;
    } else {
      cmd += ` ${outName} ${q}`;
    }
    const lines = [
      `# Module: ${activeConfig.moduleName}`,
      activeConfig.cliHint ? `# ${activeConfig.cliHint}` : "",
      `# Batch runs queued: ${n || "—"}`,
      `# Parameters: ${JSON.stringify(params)}`,
      cmd,
    ].filter(Boolean);
    cliPreview.textContent = lines.join("\n");
  }

  function updateTimeEstimate() {
    const n = Math.max(1, batchRunCount());
    const total = n * hoursPerScan;
    timeEstimateEl.textContent = `Estimated: ${n} run(s) × ${formatHours(hoursPerScan)} ≈ ${formatHours(total)} (heuristic)`;
  }

  async function loadModule() {
    try {
      const apiModules = await NeuroflowApi.fetchJson("/api/v1/modules");
      const apiModule = apiModules.find((m) => m.id === activeModuleId);
      if (apiModule) {
        hoursPerScan = apiModule.estimated_hours_per_scan || hoursPerScan;
        document.getElementById("page-title").textContent = `ITK · ${apiModule.module_name}`;
        document.getElementById("page-summary").textContent = apiModule.description;
        document.getElementById("nav-module-label").textContent = apiModule.module_name;
      }
    } catch {
      /* offline */
    }

    activeConfig = modules[activeModuleId];
    if (!activeConfig) {
      activeModuleId = "itk-diffusion-complexity-mapping";
      activeConfig = modules["itk-diffusion-complexity-mapping"];
    }

    if (!document.getElementById("page-title").textContent.includes("ITK")) {
      document.getElementById("page-title").textContent = `ITK · ${activeConfig.moduleName}`;
      document.getElementById("page-summary").textContent = activeConfig.summary;
      document.getElementById("nav-module-label").textContent = activeConfig.moduleName;
    }

    hoursPerScan = activeConfig.estimatedHours || hoursPerScan;
    const docsLink = document.getElementById("docs-link");
    const docsLabelEl = document.getElementById("docs-link-label");
    if (docsLink && activeConfig.docsUrl) docsLink.href = activeConfig.docsUrl;
    if (docsLabelEl && activeConfig.docsLabel) docsLabelEl.textContent = activeConfig.docsLabel;

    renderPrerequisites(activeConfig);
    renderInputs(activeConfig);
    renderParams(activeConfig);
    updateTimeEstimate();
    updateCliPreview();
  }

  function showError(message) {
    formError.textContent = message;
    formError.classList.remove("hidden");
  }

  function clearError() {
    formError.classList.add("hidden");
    formError.textContent = "";
  }

  function setRunningUi() {
    statusPanel.classList.remove("hidden");
    runBtn.disabled = true;
    runBtn.classList.add("opacity-50", "cursor-not-allowed");
    runBtn.innerHTML = `
      <span class="material-symbols-outlined animate-spin">refresh</span>
      Processing in background`;
    global.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  }

  function resetRunButton() {
    runBtn.disabled = false;
    runBtn.classList.remove("opacity-50", "cursor-not-allowed");
    runBtn.innerHTML = `
      <span class="material-symbols-outlined">play_arrow</span>
      Execute processing`;
  }

  function updateMonitoring(statusData, logData) {
    const label = document.getElementById("job-status-label");
    const status = logData?.status || statusData?.status || "queued";
    label.textContent = status;

    const elapsedEl = document.getElementById("elapsed-label");
    const elapsed = statusData?.elapsed_seconds ?? logData?.elapsed_seconds;
    if (elapsed != null) {
      elapsedEl.textContent = `Elapsed: ${formatDuration(elapsed)}`;
      elapsedEl.classList.remove("hidden");
    }

    const batchTotal = statusData?.batch_total || logData?.batch_total || 0;
    const batchIdx = statusData?.batch_current_index || logData?.batch_current_index || 0;
    const batchEl = document.getElementById("batch-label");
    if (batchEl) {
      if (batchTotal > 1) {
        const current = status === "completed" ? batchTotal : Math.max(1, batchIdx);
        batchEl.textContent = `Run ${current} of ${batchTotal}`;
        batchEl.classList.remove("hidden");
      } else {
        batchEl.classList.add("hidden");
      }
    }

    const etaEl = document.getElementById("eta-label");
    const remaining =
      statusData?.estimated_remaining_seconds ?? logData?.estimated_remaining_seconds;
    if (remaining != null && status === "running") {
      etaEl.textContent = `ETA (heuristic): ${formatDuration(remaining)}`;
      etaEl.classList.remove("hidden");
    } else {
      etaEl.classList.add("hidden");
    }

    if (batchTotal > 1 && batchIdx > 0) {
      progressBar.style.width = `${Math.min(100, (batchIdx / batchTotal) * 100)}%`;
    } else {
      const widths = { queued: "5%", running: "40%", completed: "100%", failed: "100%" };
      progressBar.style.width = widths[status] || "10%";
    }
    if (status === "failed" || status === "cancelled") progressBar.classList.add("bg-error");
    else progressBar.classList.remove("bg-error");

    if (global.NeuroflowJobControls) {
      global.NeuroflowJobControls.updateKillButtonVisibility(statusData, logData);
    }
  }

  async function pollJob(jobId) {
    const logData = await NeuroflowApi.fetchJson(`/api/v1/tools/itk/jobs/${jobId}/log`);
    const statusData = await NeuroflowApi.fetchJson(`/api/v1/tools/itk/jobs/${jobId}`);
    logOutput.textContent = logData.log || "(waiting for output…)";
    logOutput.scrollTop = logOutput.scrollHeight;
    updateMonitoring(statusData, logData);

    if (statusData.command_preview && !logData.log) {
      logOutput.textContent = `$ ${statusData.command_preview}\n\n`;
    }

    if (global.NeuroflowJobControls?.isTerminalStatus(logData.status)) {
      clearInterval(pollTimer);
      pollTimer = null;
      resetRunButton();
      if (
        (logData.status === "failed" || logData.status === "cancelled") &&
        statusData.error_message
      ) {
        logOutput.textContent += `\n${statusData.error_message}`;
      }
    }
  }

  if (outputPrefixInput) {
    outputPrefixInput.addEventListener("input", updateCliPreview);
  }

  async function bootstrap() {
    let config = modules[activeModuleId];
    if (!config) {
      document.getElementById("page-summary").textContent =
        "Unknown module. Open a module from the ITK package page.";
      return;
    }
    if (!config.runnable) {
      await initReadOnly(activeModuleId, config);
      return;
    }
    document.getElementById("read-only-sections")?.classList.add("hidden");
    form?.classList.remove("hidden");
    await loadModule();
  }

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    clearError();

    if (!activeConfig) {
      showError("Module configuration not loaded.");
      return;
    }

    const requiredRoles = activeConfig.inputs.filter((i) => i.required).map((i) => i.role);
    const missing = requiredRoles.filter((role) => !(filesByRole.get(role) || []).length);
    if (missing.length) {
      showError(`Missing required file(s): ${missing.join(", ")}`);
      return;
    }

    const n = batchRunCount();
    if (n < 1) {
      const driver = activeConfig.batchDriverRole;
      showError(
        driver
          ? `Add at least one file using the "${driver}" selector above (listed below the button).`
          : "Each required input must have the same number of files for batch runs."
      );
      return;
    }

    const formData = new FormData();
    const roles = [];
    for (const inputDef of activeConfig.inputs) {
      const list = filesByRole.get(inputDef.role) || [];
      for (const file of list) {
        formData.append("files", file);
        roles.push(inputDef.role);
      }
    }

    formData.append("file_roles", JSON.stringify(roles));
    formData.append("module_id", activeModuleId);
    formData.append("output_prefix", outputPrefixInput?.value.trim() || "result");
    formData.append("parameters", JSON.stringify(collectParameters()));

    setRunningUi();
    logOutput.textContent = "Submitting job…";
    updateMonitoring({ status: "queued" }, { status: "queued" });

    try {
      const { res } = await NeuroflowApi.fetchApi("/api/v1/tools/itk/jobs", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        showError(data.detail || "Failed to start job.");
        resetRunButton();
        return;
      }
      if (data.command_preview) {
        logOutput.textContent = `$ ${data.command_preview}\n\n`;
      }
      currentJobId = data.job_id;
      pollTimer = setInterval(() => pollJob(data.job_id), 2000);
      pollJob(data.job_id);
    } catch {
      showError("Could not reach the API. Start the server with NEUROFLOW_SERVE_FRONTEND=1.");
      resetRunButton();
    }
  });

  if (global.NeuroflowJobControls) {
    global.NeuroflowJobControls.wireKillButton({
      toolId: TOOL_ID,
      getJobId: () => currentJobId,
      onKilled: (jobId) => pollJob(jobId),
    });
  }

  bootstrap();
})(window);
