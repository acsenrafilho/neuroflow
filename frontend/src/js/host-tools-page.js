/**
 * Host tools help page: POST /api/v1/host/rescan and show package readiness.
 */
(function (global) {
  const PORTAL_PACKAGE_IDS = ["freesurfer", "fsl", "sct"];

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function packageLabel(packageId) {
    const labels = {
      freesurfer: "FreeSurfer",
      fsl: "FSL",
      sct: "Spinal Cord Toolbox (SCT)",
      ants: "ANTs",
      slicer: "3D Slicer",
      itk: "ITK (CSIM)",
    };
    return labels[packageId] || packageId;
  }

  function sortPackages(packages) {
    const order = [...PORTAL_PACKAGE_IDS, "ants", "slicer", "itk"];
    return [...packages].sort((a, b) => {
      const ai = order.indexOf(a.package_id);
      const bi = order.indexOf(b.package_id);
      const aRank = ai === -1 ? order.length : ai;
      const bRank = bi === -1 ? order.length : bi;
      if (aRank !== bRank) return aRank - bRank;
      return String(a.package_id).localeCompare(String(b.package_id));
    });
  }

  function renderResults(packages) {
    const rows = sortPackages(packages)
      .map((pkg) => {
        const ready = Boolean(pkg.available);
        const status = ready
          ? `<span class="inline-flex items-center gap-1 rounded-full bg-secondary/10 px-3 py-1 font-label-sm text-on-secondary-container"><span class="h-1.5 w-1.5 rounded-full bg-secondary"></span> Ready</span>`
          : `<span class="inline-flex items-center gap-1 rounded-full bg-surface-container px-3 py-1 font-label-sm text-on-surface-variant"><span class="h-1.5 w-1.5 rounded-full bg-outline"></span> Not found</span>`;
        const detail = pkg.detail ? escapeHtml(pkg.detail) : "—";
        return `<tr>
          <td class="px-4 py-3 font-medium text-on-surface">${escapeHtml(packageLabel(pkg.package_id))}</td>
          <td class="px-4 py-3">${status}</td>
          <td class="px-4 py-3 text-on-surface-variant">${detail}</td>
        </tr>`;
      })
      .join("");

    return `<div class="overflow-x-auto rounded-xl border border-outline-variant/60">
      <table class="w-full border-collapse text-left text-sm">
        <thead class="bg-surface-container-low text-xs uppercase tracking-wider text-on-surface-variant">
          <tr>
            <th class="px-4 py-3">Package</th>
            <th class="px-4 py-3">Status</th>
            <th class="px-4 py-3">Detail</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant/40 bg-surface-container-lowest">${rows}</tbody>
      </table>
    </div>
    <p class="mt-3 text-sm text-on-surface-variant">
      Return to
      <a href="/" class="text-primary underline-offset-2 hover:underline">Home</a>
      to refresh module status.
    </p>`;
  }

  async function rescanHostTools() {
    const button = document.getElementById("host-tools-rescan-btn");
    const statusEl = document.getElementById("host-tools-rescan-status");
    const resultsEl = document.getElementById("host-tools-rescan-results");
    if (!button || !statusEl || !resultsEl) return;

    button.disabled = true;
    statusEl.textContent = "Scanning host tools…";
    statusEl.className = "font-label-sm text-on-surface-variant";
    resultsEl.innerHTML = "";

    try {
      const data = await NeuroflowApi.fetchJson("/api/v1/host/rescan", { method: "POST" });
      const packages = Array.isArray(data.packages) ? data.packages : [];
      statusEl.textContent = "Scan complete.";
      statusEl.className = "font-label-sm text-secondary";
      resultsEl.innerHTML = renderResults(packages);
    } catch {
      statusEl.textContent =
        "Could not reach the NeuroFlow API. Make sure the portal is running, then try again.";
      statusEl.className = "font-label-sm text-error";
      resultsEl.innerHTML = "";
    } finally {
      button.disabled = false;
    }
  }

  function init() {
    const button = document.getElementById("host-tools-rescan-btn");
    if (!button) return;
    button.addEventListener("click", () => {
      rescanHostTools();
    });
  }

  global.HostToolsPage = { init };
})(window);
