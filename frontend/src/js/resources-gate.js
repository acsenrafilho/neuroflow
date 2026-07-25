/**
 * Host resource polling: disable Execute when RAM/CPU/queue blocks new jobs.
 */
(function (global) {
  let lastBlocked = false;
  let timer = null;
  const listeners = new Set();

  function notify(resources) {
    listeners.forEach((fn) => {
      try {
        fn(resources);
      } catch {
        /* ignore listener errors */
      }
    });
  }

  async function refresh() {
    if (!global.NeuroflowApi?.fetchJson) return null;
    try {
      const resources = await global.NeuroflowApi.fetchJson("/api/v1/host/resources");
      const blocked = resources.can_accept_job === false;
      if (blocked && !lastBlocked && resources.block_reason && global.NeuroflowToast) {
        global.NeuroflowToast.show(
          `Cannot start new jobs: ${resources.block_reason}`,
          { tone: "error" }
        );
      } else if (
        !resources.can_start_job &&
        resources.can_accept_job !== false &&
        resources.block_reason &&
        global.NeuroflowToast
      ) {
        // Informational: jobs will queue until resources free.
        if (!lastBlocked) {
          global.NeuroflowToast.show(
            `Host busy (${resources.block_reason}). New jobs will wait in the queue.`,
            { tone: "error", durationMs: 4000 }
          );
        }
      }
      lastBlocked = blocked;
      notify(resources);
      return resources;
    } catch {
      return null;
    }
  }

  function applyRunButton(runBtn, resources) {
    if (!runBtn || !resources) return;
    if (resources.can_accept_job === false) {
      runBtn.disabled = true;
      runBtn.classList.add("opacity-50", "cursor-not-allowed");
      runBtn.title = resources.block_reason || "Job queue is full";
    } else if (!runBtn.dataset.forceDisabled) {
      runBtn.disabled = false;
      runBtn.classList.remove("opacity-50", "cursor-not-allowed");
      runBtn.title = "";
    }
  }

  function start(intervalMs) {
    if (timer) return;
    refresh();
    timer = setInterval(refresh, intervalMs || 15000);
  }

  function onChange(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  global.NeuroflowResources = {
    refresh,
    start,
    onChange,
    applyRunButton,
  };
})(window);
