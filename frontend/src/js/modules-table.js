/**
 * Client-side filter, search, and sort for the Processing modules table.
 */
(function (global) {
  const PACKAGE_ICONS = {
    freesurfer: { icon: "neurology", active: true },
    fsl: { icon: "science", active: true },
    ants: { icon: "transform", active: true },
    slicer: { icon: "view_in_ar", active: true },
    itk: { icon: "filter_alt", active: true },
  };

  function statusLabel(module) {
    if (module.coming_soon && !module.available) return "Coming soon";
    if (module.available) return "Ready";
    return "Install on host";
  }

  function statusBadge(module) {
    const label = statusLabel(module);
    if (module.coming_soon && !module.available) {
      return `<span class="rounded-full bg-surface-container px-3 py-1 font-label-sm text-on-surface-variant">${label}</span>`;
    }
    if (module.available) {
      return `<span class="inline-flex items-center gap-1 rounded-full bg-secondary/10 px-3 py-1 font-label-sm text-on-secondary-container"><span class="h-1.5 w-1.5 rounded-full bg-secondary"></span> ${label}</span>`;
    }
    return `<span class="inline-flex items-center gap-1 rounded-full bg-surface-container px-3 py-1 font-label-sm text-on-surface-variant"><span class="h-1.5 w-1.5 rounded-full bg-outline"></span> ${label}</span>`;
  }

  function renderRow(module) {
    const pkg = PACKAGE_ICONS[module.package_id] || { icon: "extension", active: false };
    const iconClass = pkg.active ? "text-secondary" : "text-outline";
    const rowClass = module.coming_soon ? "opacity-70" : "hover:bg-surface-container-low/50";
    const moduleUrl = module.coming_soon
      ? null
      : `${module.page_path}?module=${encodeURIComponent(module.id)}`;
    const action = moduleUrl
      ? `<a href="${moduleUrl}" class="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 font-semibold text-on-primary transition-all hover:opacity-90"><span class="material-symbols-outlined text-sm">open_in_new</span> Open module</a>`
      : `<span class="text-on-surface-variant">—</span>`;

    return `
      <tr class="${rowClass}" data-module-id="${module.id}">
        <td class="px-6 py-4">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined ${iconClass}">${pkg.icon}</span>
            <span class="font-semibold ${module.coming_soon ? "text-on-surface" : "text-primary"}">${module.package_name}</span>
          </div>
        </td>
        <td class="px-6 py-4 font-medium text-on-surface">${module.module_name}</td>
        <td class="px-6 py-4 text-on-surface-variant">${module.description}</td>
        <td class="px-6 py-4">${statusBadge(module)}</td>
        <td class="px-6 py-4">${action}</td>
      </tr>`;
  }

  function compareValues(a, b, dir) {
    if (a < b) return dir === "asc" ? -1 : 1;
    if (a > b) return dir === "asc" ? 1 : -1;
    return 0;
  }

  class ModulesTable {
    constructor(options) {
      this.allModules = [];
      this.offline = false;
      this.filters = {
        search: "",
        package: "",
        module: "",
        status: "",
      };
      this.sort = { column: "package_name", direction: "asc" };
      this.countEl = document.getElementById(options.countId || "tools-count");
      this.tbody = document.getElementById(options.tbodyId || "tools-table-body");
      this.noteRowId = options.noteRowId || "modules-offline-note";
      this._bindControls();
    }

    _bindControls() {
      const search = document.getElementById("modules-search");
      if (search) {
        search.addEventListener("input", () => {
          this.filters.search = search.value.trim();
          this.apply();
        });
      }

      ["package", "module", "status"].forEach((key) => {
        const el = document.getElementById(`filter-${key}`);
        if (el) {
          el.addEventListener("change", () => {
            this.filters[key] = el.value;
            if (key === "package") this._refreshModuleFilterOptions();
            this.apply();
          });
        }
      });

      document.querySelectorAll("[data-sort-col]").forEach((th) => {
        th.addEventListener("click", () => {
          const col = th.dataset.sortCol;
          if (this.sort.column === col) {
            this.sort.direction = this.sort.direction === "asc" ? "desc" : "asc";
          } else {
            this.sort.column = col;
            this.sort.direction = "asc";
          }
          this._updateSortIndicators();
          this.apply();
        });
      });
    }

    _updateSortIndicators() {
      document.querySelectorAll("[data-sort-col]").forEach((th) => {
        const col = th.dataset.sortCol;
        if (col === this.sort.column) {
          th.setAttribute("aria-sort", this.sort.direction === "asc" ? "ascending" : "descending");
          th.dataset.sortActive = "true";
        } else {
          th.setAttribute("aria-sort", "none");
          delete th.dataset.sortActive;
        }
      });
    }

    setModules(modules, offline) {
      this.allModules = modules;
      this.offline = offline;
      this._populateFilterOptions();
      this._updateSortIndicators();
      this.apply();
    }

    _populateFilterOptions() {
      const packageSelect = document.getElementById("filter-package");
      const moduleSelect = document.getElementById("filter-module");
      if (!packageSelect || !moduleSelect) return;

      const packages = [...new Set(this.allModules.map((m) => m.package_name))].sort();
      packageSelect.innerHTML =
        '<option value="">All packages</option>' +
        packages.map((p) => `<option value="${p}">${p}</option>`).join("");

      this._refreshModuleFilterOptions();
    }

    _refreshModuleFilterOptions() {
      const moduleSelect = document.getElementById("filter-module");
      if (!moduleSelect) return;

      let scoped = this.allModules;
      if (this.filters.package) {
        scoped = scoped.filter((m) => m.package_name === this.filters.package);
      }
      const modules = [...new Set(scoped.map((m) => m.module_name))].sort();
      const current = this.filters.module;
      moduleSelect.innerHTML =
        '<option value="">All modules</option>' +
        modules.map((m) => `<option value="${m}">${m}</option>`).join("");
      if (current && modules.includes(current)) {
        moduleSelect.value = current;
      } else {
        this.filters.module = "";
        moduleSelect.value = "";
      }
    }

    _filteredModules() {
      return this.allModules.filter((m) => {
        if (this.filters.package && m.package_name !== this.filters.package) return false;
        if (this.filters.module && m.module_name !== this.filters.module) return false;
        if (this.filters.status) {
          const label = statusLabel(m);
          if (label !== this.filters.status) return false;
        }
        if (this.filters.search) {
          const hay = `${m.package_name} ${m.module_name} ${m.description} ${statusLabel(m)}`.toLowerCase();
          if (!hay.includes(this.filters.search.toLowerCase())) return false;
        }
        return true;
      });
    }

    _sortedModules(modules) {
      const col = this.sort.column;
      const dir = this.sort.direction;
      return [...modules].sort((a, b) => {
        let av;
        let bv;
        if (col === "status") {
          av = statusLabel(a);
          bv = statusLabel(b);
        } else {
          av = a[col] ?? "";
          bv = b[col] ?? "";
        }
        const primary = compareValues(String(av).toLowerCase(), String(bv).toLowerCase(), dir);
        if (primary !== 0) return primary;
        return compareValues(
          a.module_name.toLowerCase(),
          b.module_name.toLowerCase(),
          "asc"
        );
      });
    }

    apply() {
      const filtered = this._sortedModules(this._filteredModules());
      const total = this.allModules.length;
      const showing = filtered.length;

      if (this.countEl) {
        const ready = this.allModules.filter((m) => m.available && !m.coming_soon).length;
        const base = this.offline
          ? `${total} modules (start API on :8000 for live status)`
          : `${ready} of ${total} modules ready on this host`;
        this.countEl.textContent = `Showing ${showing} of ${total} · ${base}`;
        this.countEl.setAttribute("aria-live", "polite");
      }

      if (!this.tbody) return;

      if (showing === 0) {
        this.tbody.innerHTML = `
          <tr>
            <td class="px-6 py-8 text-center text-on-surface-variant" colspan="5">
              No modules match the current filters.
            </td>
          </tr>`;
      } else {
        this.tbody.innerHTML = filtered.map(renderRow).join("");
      }

      const existingNote = document.getElementById(this.noteRowId);
      if (existingNote) existingNote.remove();

      if (this.offline && showing > 0) {
        const note = document.createElement("tr");
        note.id = this.noteRowId;
        note.innerHTML = `
          <td class="px-6 py-3 text-xs text-on-surface-variant" colspan="5">
            Showing catalog offline. Run <code class="rounded bg-surface-container px-1">make api</code>
            with <code class="rounded bg-surface-container px-1">NEUROFLOW_SERVE_FRONTEND=1</code>
            or open <a href="http://127.0.0.1:8000/" class="text-secondary hover:underline">http://127.0.0.1:8000/</a>.
          </td>`;
        this.tbody.appendChild(note);
      }
    }
  }

  global.ModulesTable = ModulesTable;
  global.ModulesTableRender = { renderRow, statusBadge, statusLabel, PACKAGE_ICONS };
})(window);
