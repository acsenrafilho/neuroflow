/**
 * Home page panel: list / create workspaces and open folders on the host.
 */
(function (global) {
  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function truncatePath(path, maxLen) {
    const text = String(path || "");
    const limit = maxLen || 48;
    if (text.length <= limit) return text;
    return `…${text.slice(-(limit - 1))}`;
  }

  async function apiJson(path, options) {
    const { res } = await NeuroflowApi.fetchApi(path, options);
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    return data;
  }

  async function apiRequest(path, options) {
    let lastError = null;
    for (const base of NeuroflowApi.candidateBases()) {
      try {
        const res = await fetch(`${base}${path}`, options);
        sessionStorage.setItem("neuroflow_api_base", base);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const detail = data.detail;
          const message =
            typeof detail === "string"
              ? detail
              : Array.isArray(detail)
                ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
                : `HTTP ${res.status}`;
          throw new Error(message);
        }
        return data;
      } catch (err) {
        if (err instanceof TypeError) {
          lastError = err;
          continue;
        }
        throw err;
      }
    }
    throw lastError || new Error("API unavailable");
  }

  function WorkspacesPanel(options) {
    this.tbodyId = options?.tbodyId || "workspaces-body";
    this.countId = options?.countId || "workspaces-count";
    this.formId = options?.formId || "workspace-create-form";
    this.inputId = options?.inputId || "workspace-create-name";
    this.statusId = options?.statusId || "workspaces-status";
  }

  WorkspacesPanel.prototype.statusEl = function () {
    return document.getElementById(this.statusId);
  };

  WorkspacesPanel.prototype.setStatus = function (message, tone) {
    const el = this.statusEl();
    if (!el) return;
    el.textContent = message || "";
    el.className =
      tone === "error"
        ? "font-label-sm text-error"
        : tone === "success"
          ? "font-label-sm text-secondary"
          : "font-label-sm text-on-surface-variant";
  };

  WorkspacesPanel.prototype.currentWorkspace = function () {
    return NeuroflowWorkspace.getWorkspace();
  };

  WorkspacesPanel.prototype.renderRows = function (workspaces) {
    const tbody = document.getElementById(this.tbodyId);
    const count = document.getElementById(this.countId);
    if (!tbody) return;

    const current = this.currentWorkspace();
    if (count) {
      count.textContent =
        workspaces.length === 1 ? "1 workspace" : `${workspaces.length} workspaces`;
    }

    if (!workspaces.length) {
      tbody.innerHTML = `<tr><td class="px-6 py-6 text-center text-on-surface-variant" colspan="4">No workspaces yet. Create one above.</td></tr>`;
      return;
    }

    tbody.innerHTML = workspaces
      .map((ws) => {
        const isCurrent = current && current === ws.name;
        const rowClass = isCurrent
          ? "bg-primary/5 hover:bg-primary/10"
          : "hover:bg-surface-container-low/50";
        const badge = isCurrent
          ? `<span class="ml-2 rounded bg-primary/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary">Current</span>`
          : "";
        return `<tr class="${rowClass}" data-workspace="${escapeHtml(ws.name)}">
          <td class="px-6 py-3 font-medium">
            <span class="font-code-mono text-sm">${escapeHtml(ws.name)}</span>${badge}
          </td>
          <td class="px-6 py-3">${ws.subject_count}</td>
          <td class="px-6 py-3 font-code-mono text-xs text-on-surface-variant" title="${escapeHtml(ws.path)}">${escapeHtml(truncatePath(ws.path))}</td>
          <td class="px-6 py-3">
            <div class="flex flex-wrap items-center gap-2">
              <button type="button" data-action="use" class="inline-flex items-center gap-1 rounded-lg border border-outline-variant px-3 py-1.5 font-label-sm font-semibold text-on-surface hover:bg-surface-container">
                Use
              </button>
              <button type="button" data-action="open" class="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 font-label-sm font-semibold text-on-primary hover:opacity-90">
                <span class="material-symbols-outlined text-sm">folder_open</span>
                Open folder
              </button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  };

  WorkspacesPanel.prototype.load = async function () {
    const count = document.getElementById(this.countId);
    try {
      const workspaces = await apiJson("/api/v1/workspaces");
      this.renderRows(workspaces || []);
    } catch {
      if (count) count.textContent = "Unavailable";
      const tbody = document.getElementById(this.tbodyId);
      if (tbody) {
        tbody.innerHTML = `<tr><td class="px-6 py-6 text-center text-on-surface-variant" colspan="4">Could not load workspaces.</td></tr>`;
      }
    }
  };

  WorkspacesPanel.prototype.create = async function (rawName) {
    const safe = NeuroflowWorkspace.sanitizeWorkspace(rawName);
    if (!safe) {
      throw new Error("Enter a Project / User name (letters, numbers, _ or -).");
    }
    const created = await apiRequest("/api/v1/workspaces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: safe }),
    });
    NeuroflowWorkspace.setWorkspace(created.name);
    return created;
  };

  WorkspacesPanel.prototype.useWorkspace = function (name) {
    const safe = NeuroflowWorkspace.setWorkspace(name);
    this.setStatus(`Using workspace “${safe}” for new jobs.`, "success");
    if (global.NeuroflowToast) {
      NeuroflowToast.show(`Workspace set to ${safe}`, { tone: "success", durationMs: 3000 });
    }
    this.load();
  };

  WorkspacesPanel.prototype.openFolder = async function (name) {
    await apiRequest(`/api/v1/workspaces/${encodeURIComponent(name)}/open`, {
      method: "POST",
    });
    this.setStatus(`Opened folder for “${name}” in the file manager.`, "success");
    if (global.NeuroflowToast) {
      NeuroflowToast.show(`Opened ${name} folder`, { tone: "success", durationMs: 3000 });
    }
  };

  WorkspacesPanel.prototype.bind = function () {
    const form = document.getElementById(this.formId);
    const input = document.getElementById(this.inputId);
    const tbody = document.getElementById(this.tbodyId);

    if (form && input) {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        this.setStatus("Creating…");
        try {
          const created = await this.create(input.value);
          input.value = created.name;
          this.setStatus(`Workspace “${created.name}” ready.`, "success");
          if (global.NeuroflowToast) {
            NeuroflowToast.show(`Workspace ${created.name} created`, {
              tone: "success",
              durationMs: 3000,
            });
          }
          await this.load();
        } catch (err) {
          const message = err?.message || "Could not create workspace.";
          this.setStatus(message, "error");
          if (global.NeuroflowToast) {
            NeuroflowToast.show(message, { tone: "error" });
          }
        }
      });
    }

    if (tbody) {
      tbody.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const row = button.closest("tr[data-workspace]");
        if (!row) return;
        const name = row.getAttribute("data-workspace");
        const action = button.getAttribute("data-action");
        try {
          if (action === "use") {
            this.useWorkspace(name);
          } else if (action === "open") {
            button.disabled = true;
            await this.openFolder(name);
          }
        } catch (err) {
          const message = err?.message || "Action failed.";
          this.setStatus(message, "error");
          if (global.NeuroflowToast) {
            NeuroflowToast.show(message, { tone: "error" });
          }
        } finally {
          button.disabled = false;
        }
      });
    }
  };

  WorkspacesPanel.prototype.init = function () {
    this.bind();
    this.load();
  };

  global.WorkspacesPanel = WorkspacesPanel;
})(window);
