/**
 * Workspace (project/user) name persisted in localStorage.
 */
(function (global) {
  const STORAGE_KEY = "neuroflow_workspace";

  function sanitizeWorkspace(name) {
    return String(name || "")
      .trim()
      .replace(/\s+/g, "_")
      .replace(/[^a-zA-Z0-9_-]/g, "");
  }

  function normalizeSubjectId(value) {
    let cleaned = String(value || "").trim();
    if (!cleaned) return "";
    cleaned = cleaned.replace(/\s+/g, "_");
    if (!/^sub-/i.test(cleaned)) {
      cleaned = `sub-${cleaned}`;
    }
    return cleaned;
  }

  function getWorkspace() {
    return localStorage.getItem(STORAGE_KEY) || "";
  }

  function setWorkspace(name) {
    const safe = sanitizeWorkspace(name);
    if (safe) localStorage.setItem(STORAGE_KEY, safe);
    return safe;
  }

  function requireWorkspace() {
    const current = sanitizeWorkspace(getWorkspace());
    if (!current) {
      throw new Error("Enter a Project / User name (workspace) before running.");
    }
    setWorkspace(current);
    return current;
  }

  function bindWorkspaceInput(inputId) {
    const el = document.getElementById(inputId || "workspace");
    if (!el) return null;
    const saved = getWorkspace();
    if (saved && !el.value) el.value = saved;
    el.addEventListener("change", () => {
      const safe = sanitizeWorkspace(el.value);
      el.value = safe;
      if (safe) setWorkspace(safe);
    });
    el.addEventListener("blur", () => {
      const safe = sanitizeWorkspace(el.value);
      el.value = safe;
      if (safe) setWorkspace(safe);
    });
    return el;
  }

  global.NeuroflowWorkspace = {
    STORAGE_KEY,
    sanitizeWorkspace,
    normalizeSubjectId,
    getWorkspace,
    setWorkspace,
    requireWorkspace,
    bindWorkspaceInput,
  };
})(window);
