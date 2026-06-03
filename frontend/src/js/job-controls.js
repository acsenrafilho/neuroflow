/**
 * Shared job kill controls for tool pages with subprocess execution.
 */
(function (global) {
  function updateKillButtonVisibility(statusData, logData) {
    const btn = document.getElementById("kill-job-btn");
    if (!btn) return;

    const status = logData?.status || statusData?.status || "queued";
    if (status === "running" && !btn.disabled) {
      btn.classList.remove("hidden");
      return;
    }

    if (status !== "running") {
      btn.classList.add("hidden");
      btn.disabled = false;
    }
  }

  function wireKillButton({ toolId, getJobId, onKilled }) {
    const btn = document.getElementById("kill-job-btn");
    if (!btn || !global.NeuroflowApi?.killJob) return;

    btn.addEventListener("click", async () => {
      const jobId = getJobId();
      if (!jobId) return;
      if (!confirm("Stop this job? The running process will be terminated.")) return;

      btn.disabled = true;
      try {
        await global.NeuroflowApi.killJob(toolId, jobId);
        if (onKilled) onKilled(jobId);
      } catch (err) {
        btn.disabled = false;
        alert(err.message || "Could not stop the job.");
      }
    });
  }

  function isTerminalStatus(status) {
    return status === "completed" || status === "failed" || status === "cancelled";
  }

  global.NeuroflowJobControls = {
    wireKillButton,
    updateKillButtonVisibility,
    isTerminalStatus,
  };
})(window);
