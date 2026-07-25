/**
 * Lightweight toast notifications.
 */
(function (global) {
  let container = null;

  function ensureContainer() {
    if (container) return container;
    container = document.createElement("div");
    container.id = "neuroflow-toaster";
    container.setAttribute("aria-live", "polite");
    container.className =
      "pointer-events-none fixed bottom-6 right-6 z-[100] flex w-full max-w-sm flex-col gap-2";
    document.body.appendChild(container);
    return container;
  }

  function show(message, options) {
    const opts = options || {};
    const host = ensureContainer();
    const toast = document.createElement("div");
    const tone =
      opts.tone === "error"
        ? "border-error/40 bg-error/10 text-error"
        : opts.tone === "success"
          ? "border-secondary/40 bg-secondary/10 text-on-secondary-container"
          : "border-outline-variant bg-surface-container-lowest text-on-surface";
    toast.className = `pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-lg ${tone}`;
    toast.textContent = message;
    host.appendChild(toast);
    const ttl = opts.durationMs == null ? 6000 : opts.durationMs;
    if (ttl > 0) {
      setTimeout(() => {
        toast.remove();
      }, ttl);
    }
    return toast;
  }

  global.NeuroflowToast = { show };
})(window);
