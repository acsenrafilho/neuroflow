/**
 * Multi-job session list + polling helpers for tool pages.
 */
(function (global) {
  function formatDuration(seconds) {
    const s = Math.max(0, Math.floor(seconds || 0));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
  }

  class JobSessionList {
    constructor(options) {
      this.toolId = options.toolId;
      this.listEl = document.getElementById(options.listId || "jobs-session-list");
      this.logOutput = document.getElementById(options.logId || "log-output");
      this.statusPanel = document.getElementById(options.statusPanelId || "status-panel");
      this.jobs = new Map();
      this.focusedJobId = null;
      this.pollTimer = null;
    }

    add(job) {
      this.jobs.set(job.jobId, {
        jobId: job.jobId,
        subjectId: job.subjectId || "",
        status: job.status || "queued",
        elapsed: null,
      });
      this.focusedJobId = job.jobId;
      if (this.statusPanel) this.statusPanel.classList.remove("hidden");
      this.render();
      this.ensurePolling();
    }

    focus(jobId) {
      if (!this.jobs.has(jobId)) {
        this.add({ jobId, status: "queued" });
      }
      this.focusedJobId = jobId;
      this.render();
      this.pollOnce(jobId);
    }

    ensurePolling() {
      if (this.pollTimer) return;
      this.pollTimer = setInterval(() => this.pollAll(), 2000);
      this.pollAll();
    }

    async pollAll() {
      const ids = [...this.jobs.keys()];
      for (const id of ids) {
        await this.pollOnce(id);
      }
      const active = [...this.jobs.values()].some(
        (j) => j.status === "running" || j.status === "queued"
      );
      if (!active && this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    }

    async pollOnce(jobId) {
      if (!global.NeuroflowApi?.fetchJson) return;
      try {
        const logData = await global.NeuroflowApi.fetchJson(
          `/api/v1/tools/${this.toolId}/jobs/${jobId}/log`
        );
        const statusData = await global.NeuroflowApi.fetchJson(
          `/api/v1/tools/${this.toolId}/jobs/${jobId}`
        );
        const entry = this.jobs.get(jobId) || { jobId };
        entry.status = logData.status || statusData.status || entry.status;
        entry.elapsed = statusData.elapsed_seconds ?? logData.elapsed_seconds;
        entry.subjectId =
          entry.subjectId ||
          statusData.subject_id ||
          statusData.parameters?.subject_id ||
          (statusData.batch_items && statusData.batch_items[0]?.subject_id) ||
          "";
        this.jobs.set(jobId, entry);
        if (jobId === this.focusedJobId && this.logOutput) {
          this.logOutput.textContent = logData.log || "(waiting for output…)";
          this.logOutput.scrollTop = this.logOutput.scrollHeight;
          const label = document.getElementById("job-status-label");
          if (label) label.textContent = entry.status;
          const elapsedEl = document.getElementById("elapsed-label");
          if (elapsedEl && entry.elapsed != null) {
            elapsedEl.textContent = `Elapsed: ${formatDuration(entry.elapsed)}`;
            elapsedEl.classList.remove("hidden");
          }
          const batchTotal = statusData.batch_total || logData.batch_total || 0;
          const batchIdx = statusData.batch_current_index || logData.batch_current_index || 0;
          const batchEl = document.getElementById("batch-label");
          if (batchEl) {
            if (batchTotal > 1) {
              const current =
                entry.status === "completed" ? batchTotal : Math.max(1, batchIdx);
              batchEl.textContent = `Run ${current} of ${batchTotal}`;
              batchEl.classList.remove("hidden");
            } else {
              batchEl.classList.add("hidden");
            }
          }
          const progressBar = document.getElementById("progress-bar");
          if (progressBar) {
            if (batchTotal > 1 && batchIdx > 0) {
              progressBar.style.width = `${Math.min(100, (batchIdx / batchTotal) * 100)}%`;
            } else {
              const widths = {
                queued: "5%",
                running: "40%",
                completed: "100%",
                failed: "100%",
                cancelled: "100%",
              };
              progressBar.style.width = widths[entry.status] || "10%";
            }
          }
        }
        this.render();
      } catch {
        /* ignore transient poll errors */
      }
    }

    render() {
      if (!this.listEl) return;
      if (this.jobs.size === 0) {
        this.listEl.innerHTML = "";
        return;
      }
      const rows = [...this.jobs.values()]
        .map((job) => {
          const focused = job.jobId === this.focusedJobId;
          const stopDisabled =
            job.status !== "running"
              ? "disabled"
              : "";
          return `
            <tr class="${focused ? "bg-primary/5" : ""}" data-job-id="${job.jobId}">
              <td class="px-3 py-2 font-code-mono text-xs">${job.jobId}</td>
              <td class="px-3 py-2 text-sm">${job.subjectId || "—"}</td>
              <td class="px-3 py-2 text-sm">${job.status}</td>
              <td class="px-3 py-2 text-sm">${job.elapsed != null ? formatDuration(job.elapsed) : "—"}</td>
              <td class="px-3 py-2">
                <button type="button" data-action="focus" data-job-id="${job.jobId}"
                  class="mr-2 rounded border border-outline-variant px-2 py-0.5 text-xs hover:bg-surface-container">
                  View log
                </button>
                <button type="button" data-action="stop" data-job-id="${job.jobId}" ${stopDisabled}
                  class="rounded border border-error/40 px-2 py-0.5 text-xs text-error hover:bg-error/10 disabled:opacity-40">
                  Stop
                </button>
              </td>
            </tr>`;
        })
        .join("");
      this.listEl.innerHTML = `
        <div class="mb-3 overflow-x-auto rounded-lg border border-outline-variant">
          <table class="w-full text-left text-sm">
            <thead class="bg-surface-container-low text-xs uppercase text-on-surface-variant">
              <tr>
                <th class="px-3 py-2">Job</th>
                <th class="px-3 py-2">Subject</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Elapsed</th>
                <th class="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
      this.listEl.querySelectorAll("[data-action=focus]").forEach((btn) => {
        btn.addEventListener("click", () => this.focus(btn.getAttribute("data-job-id")));
      });
      this.listEl.querySelectorAll("[data-action=stop]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const jobId = btn.getAttribute("data-job-id");
          if (!jobId || !global.NeuroflowApi?.killJob) return;
          if (!confirm("Stop this job? The running process will be terminated.")) return;
          try {
            await global.NeuroflowApi.killJob(this.toolId, jobId);
            await this.pollOnce(jobId);
          } catch (err) {
            alert(err.message || "Could not stop the job.");
          }
        });
      });
    }
  }

  global.NeuroflowJobSession = { JobSessionList, formatDuration };
})(window);
