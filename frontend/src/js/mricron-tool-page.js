/**
 * MRIcron dcm2niix page: one DICOM series, fixed command, job log.
 */
(function (global) {
  const form = document.getElementById("job-form");
  const runBtn = document.getElementById("run-btn");
  const statusPanel = document.getElementById("status-panel");
  const logOutput = document.getElementById("log-output");
  const formError = document.getElementById("form-error");
  const cliPreview = document.getElementById("cli-preview");
  const fileInput = document.getElementById("dicom-input");
  const fileList = document.getElementById("file-list");
  const subjectIdInput = document.getElementById("subject_id");
  const copyToAnat = document.getElementById("copy-to-anat");

  const queryParams = new URLSearchParams(global.location.search);
  const queryJobId = queryParams.get("job_id");
  const TOOL_ID = "mricron";
  const jobSession = global.NeuroflowJobSession
    ? new global.NeuroflowJobSession.JobSessionList({ toolId: TOOL_ID })
    : null;

  /** @type {File[]} */
  let selectedFiles = [];

  if (global.NeuroflowWorkspace) {
    global.NeuroflowWorkspace.bindWorkspaceInput("workspace");
  }
  if (global.NeuroflowResources) {
    global.NeuroflowResources.start(15000);
    global.NeuroflowResources.onChange((res) => {
      global.NeuroflowResources.applyRunButton(runBtn, res);
    });
  }

  function previewCommand() {
    const copy = copyToAnat?.checked ? "yes" : "no";
    const names = selectedFiles.map((file) => file.name);
    const lines = [
      "# Fixed dcm2niix command (patient name, protocol, series)",
      "dcm2niix -z y -b y -ba y -f %n_%p_%s -o <derivatives/mricron/dcm2niix> <dicom-series>",
      `# Also copy NIfTI into anat/: ${copy}`,
    ];
    if (names.length) {
      lines.push(`# Files: ${names.join(", ")}`);
    }
    if (cliPreview) cliPreview.textContent = lines.join("\n");
  }

  function renderFileList() {
    if (!fileList) return;
    if (selectedFiles.length === 0) {
      fileList.textContent = "No file selected";
      fileList.className = "text-xs text-on-surface-variant";
      return;
    }
    fileList.className = "text-xs text-on-surface";
    fileList.innerHTML = selectedFiles
      .map(
        (file, idx) =>
          `<div class="flex items-center justify-between gap-2 py-1">
            <span class="truncate">${file.name}</span>
            <button type="button" class="remove-dicom text-on-surface-variant hover:text-error" data-index="${idx}" title="Remove">
              <span class="material-symbols-outlined text-sm">close</span>
            </button>
          </div>`
      )
      .join("");
    fileList.querySelectorAll(".remove-dicom").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectedFiles.splice(Number(btn.dataset.index), 1);
        renderFileList();
        previewCommand();
      });
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      const picked = Array.from(fileInput.files || []);
      for (const file of picked) {
        if (
          !selectedFiles.some(
            (existing) =>
              existing.name === file.name &&
              existing.size === file.size &&
              existing.lastModified === file.lastModified
          )
        ) {
          selectedFiles.push(file);
        }
      }
      fileInput.value = "";
      renderFileList();
      previewCommand();
    });
  }

  if (copyToAnat) {
    copyToAnat.addEventListener("change", previewCommand);
  }

  function showError(message) {
    if (!formError) return;
    formError.textContent = message;
    formError.classList.remove("hidden");
  }

  function clearError() {
    if (!formError) return;
    formError.classList.add("hidden");
    formError.textContent = "";
  }

  function resetRunButton() {
    if (!runBtn) return;
    runBtn.dataset.forceDisabled = "";
    runBtn.disabled = false;
    runBtn.classList.remove("opacity-50", "cursor-not-allowed");
    runBtn.innerHTML = `
      <span class="material-symbols-outlined">play_arrow</span>
      Execute processing`;
  }

  previewCommand();

  if (queryJobId && jobSession) {
    jobSession.focus(queryJobId);
    if (statusPanel) statusPanel.classList.remove("hidden");
  }

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    event.stopPropagation();
    clearError();

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

    if (selectedFiles.length === 0) {
      showError("Add DICOM files (.dcm) or one ZIP of a single series.");
      return;
    }

    const formData = new FormData();
    for (const file of selectedFiles) {
      formData.append("files", file);
    }
    formData.append("workspace", workspace);
    formData.append("subject_id", subjectId);
    formData.append("copy_to_anat", copyToAnat?.checked ? "true" : "false");

    if (statusPanel) statusPanel.classList.remove("hidden");
    if (runBtn) {
      runBtn.dataset.forceDisabled = "1";
      runBtn.disabled = true;
    }
    if (logOutput) logOutput.textContent = "Submitting job…";

    try {
      const { res } = await NeuroflowApi.fetchApi("/api/v1/tools/mricron/jobs", {
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
      if (logOutput && data.command_preview) {
        logOutput.textContent = `$ ${data.command_preview}\n\n`;
      }
      if (jobSession) {
        jobSession.add({
          jobId: data.job_id,
          subjectId,
          status: data.status || "queued",
        });
      }
      selectedFiles = [];
      renderFileList();
      previewCommand();
      resetRunButton();
      global.NeuroflowResources?.refresh();
    } catch {
      showError("Could not reach the NeuroFlow API.");
      resetRunButton();
    }
  });
})(window);
