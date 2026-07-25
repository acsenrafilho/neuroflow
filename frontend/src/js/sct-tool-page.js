/**
 * SCT tool page: dynamic form per module, batch uploads, job submit, log polling.
 */
(function (global) {
  const modules = global.SCT_MODULES || {};

  const form = document.getElementById("job-form");
  const runBtn = document.getElementById("run-btn");
  const statusPanel = document.getElementById("status-panel");
  const logOutput = document.getElementById("log-output");
  const formError = document.getElementById("form-error");
  const prerequisitesEl = document.getElementById("prerequisites-panel");
  const prerequisitesList = document.getElementById("prerequisites-list");
  const inputsSection = document.getElementById("inputs-section");
  const paramsSection = document.getElementById("params-section");
  const paramsGrid = document.getElementById("params-grid");
  const cliPreview = document.getElementById("cli-preview");
  const outputPrefixInput = document.getElementById("output_prefix");
  const timeEstimateEl = document.getElementById("time-estimate");
  const subjectIdInput = document.getElementById("subject_id");

  const queryParams = new URLSearchParams(global.location.search);
  const queryModuleId = queryParams.get("module");
  const queryJobId = queryParams.get("job_id");
  let activeConfig = null;
  let activeModuleId = queryModuleId || "sct-deepseg";
  const TOOL_ID = "sct";
  const jobSession = global.NeuroflowJobSession
    ? new global.NeuroflowJobSession.JobSessionList({ toolId: TOOL_ID })
    : null;

  /** @type {Map<string, File[]>} */
  const filesByRole = new Map();

  if (global.NeuroflowWorkspace) {
    global.NeuroflowWorkspace.bindWorkspaceInput("workspace");
  }
  if (global.NeuroflowResources) {
    global.NeuroflowResources.start(15000);
    global.NeuroflowResources.onChange((res) => {
      global.NeuroflowResources.applyRunButton(runBtn, res);
    });
  }

  function modulePageUrl(moduleId) {
    return `/tools/sct.html?module=${encodeURIComponent(moduleId)}`;
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
            ? `<a href="${modulePageUrl(step.moduleId)}" class="font-semibold text-secondary hover:underline">${step.moduleId.replace("sct-", "").toUpperCase()} module</a>`
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
          class="sct-file-input rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-2 text-sm"
          data-role="${inputDef.role}"
          accept="${inputDef.accept || ".nii,.nii.gz,.gz"}"
          ${multi ? "multiple" : ""}
        />
        <div class="file-list" data-filename="${inputDef.role}"></div>
      `;
      inputsSection.appendChild(block);

      const fileInput = block.querySelector(".sct-file-input");
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
    const lines = [
      `# Module: ${activeConfig.moduleName}`,
      `# Output prefix: ${prefix}`,
      `# Batch runs queued: ${n || "—"}`,
    ];
    filesByRole.forEach((files, role) => {
      files.forEach((file) => lines.push(`# ${role}: ${file.name}`));
    });
    lines.push(`# Parameters: ${JSON.stringify(params)}`);
    const exe =
      activeModuleId === "sct-deepseg"
        ? `sct_deepseg ${params.task || "spinalcord"}`
        : activeModuleId.replace("sct-", "sct_").replace(/-/g, "_");
    lines.push(`${exe} … (same command per input, run sequentially on host)`);
    cliPreview.textContent = lines.join("\n");
  }

  function updateTimeEstimate() {
    if (timeEstimateEl) {
      timeEstimateEl.textContent = "";
      timeEstimateEl.classList.add("hidden");
    }
  }

  async function loadModule() {
    try {
      const apiModules = await NeuroflowApi.fetchJson("/api/v1/modules");
      const apiModule = apiModules.find((m) => m.id === activeModuleId);
      if (apiModule) {
        document.getElementById("page-title").textContent = `SCT · ${apiModule.module_name}`;
        document.getElementById("page-summary").textContent = apiModule.description;
        document.getElementById("nav-module-label").textContent = apiModule.module_name;
      }
    } catch {
      /* offline */
    }

    activeConfig = modules[activeModuleId];
    if (!activeConfig) {
      activeModuleId = "sct-deepseg";
      activeConfig = modules["sct-deepseg"];
    }

    if (!document.getElementById("page-title").textContent.includes("SCT")) {
      document.getElementById("page-title").textContent = `SCT · ${activeConfig.moduleName}`;
      document.getElementById("page-summary").textContent = activeConfig.summary;
      document.getElementById("nav-module-label").textContent = activeConfig.moduleName;
    }

    const docsLink = document.getElementById("docs-link");
    if (docsLink && activeConfig.docsUrl) {
      docsLink.href = activeConfig.docsUrl;
      docsLink.textContent = activeConfig.docsLabel || "SCT documentation";
    }

    renderPrerequisites(activeConfig);
    renderInputs(activeConfig);
    renderParams(activeConfig);
    updateTimeEstimate();
    updateCliPreview();

    if (queryJobId && jobSession) {
      jobSession.focus(queryJobId);
    }
  }

  function showError(message) {
    formError.textContent = message;
    formError.classList.remove("hidden");
  }

  function clearError() {
    formError.classList.add("hidden");
    formError.textContent = "";
  }

  function resetRunButton() {
    runBtn.dataset.forceDisabled = "";
    runBtn.disabled = false;
    runBtn.classList.remove("opacity-50", "cursor-not-allowed");
    runBtn.innerHTML = `
      <span class="material-symbols-outlined">play_arrow</span>
      Execute processing`;
  }

  function clearPrimaryInputs() {
    filesByRole.clear();
    if (activeConfig) renderInputs(activeConfig);
    updateCliPreview();
  }

  if (outputPrefixInput) {
    outputPrefixInput.addEventListener("input", updateCliPreview);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    clearError();

    if (!activeConfig) {
      showError("Module configuration not loaded.");
      return;
    }

    let workspace;
    try {
      workspace = global.NeuroflowWorkspace
        ? global.NeuroflowWorkspace.requireWorkspace()
        : document.getElementById("workspace")?.value?.trim();
    } catch (err) {
      showError(err.message || "Workspace is required.");
      return;
    }
    if (!workspace) {
      showError("Enter a Project / User name before running.");
      return;
    }

    const rawSubject = subjectIdInput?.value?.trim() || "";
    const subjectId = global.NeuroflowWorkspace
      ? global.NeuroflowWorkspace.normalizeSubjectId(rawSubject)
      : rawSubject;
    if (!subjectId) {
      showError("Enter a Subject ID (e.g. sub-001).");
      return;
    }
    if (subjectIdInput) subjectIdInput.value = subjectId;

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
    formData.append("workspace", workspace);
    formData.append("subject_id", subjectId);
    formData.append("output_prefix", outputPrefixInput?.value.trim() || "result");
    formData.append("parameters", JSON.stringify(collectParameters()));

    statusPanel.classList.remove("hidden");
    runBtn.dataset.forceDisabled = "1";
    runBtn.disabled = true;
    logOutput.textContent = "Submitting job…";

    try {
      const { res } = await NeuroflowApi.fetchApi("/api/v1/tools/sct/jobs", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        showError(data.detail || "Failed to start job.");
        if (data.code === "resource_exhausted" || data.code === "queue_full") {
          global.NeuroflowToast?.show(data.detail, { tone: "error" });
        }
        resetRunButton();
        return;
      }
      if (data.command_preview) {
        logOutput.textContent = `$ ${data.command_preview}\n\n`;
      }
      if (jobSession) {
        jobSession.add({
          jobId: data.job_id,
          subjectId,
          status: data.status || "queued",
        });
      }
      clearPrimaryInputs();
      resetRunButton();
      global.NeuroflowResources?.refresh();
    } catch {
      showError("Could not reach the API. Start the server with NEUROFLOW_SERVE_FRONTEND=1.");
      resetRunButton();
    }
  });

  loadModule();
})(window);
