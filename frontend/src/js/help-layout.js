/**
 * Shared wiki topic nav for /help/ pages. Requires HubLayout.
 */
(function (global) {
  const TOPICS = [
    { id: "index", href: "/help/", label: "Overview" },
    { id: "concepts", href: "/help/concepts.html", label: "Concepts" },
    { id: "first-job", href: "/help/first-job.html", label: "First job" },
    { id: "workspaces", href: "/help/workspaces.html", label: "Workspaces" },
    { id: "modules", href: "/help/modules.html", label: "Modules" },
    { id: "jobs-and-logs", href: "/help/jobs-and-logs.html", label: "Jobs & logs" },
    { id: "host-tools", href: "/help/host-tools.html", label: "Host tools" },
    { id: "data-and-privacy", href: "/help/data-and-privacy.html", label: "Data & privacy" },
  ];

  function renderWikiNav(activeId) {
    const el = document.getElementById("help-wiki-nav");
    if (!el) return;

    el.innerHTML = `
      <p class="mb-3 font-label-sm uppercase tracking-wider text-on-surface-variant">User guide</p>
      <ul class="space-y-1">
        ${TOPICS.map((topic) => {
          const active = topic.id === activeId;
          const cls = active
            ? "border-primary bg-primary/10 font-semibold text-primary"
            : "border-transparent text-on-surface-variant hover:bg-surface-container hover:text-on-surface";
          return `
            <li>
              <a href="${topic.href}"
                class="block border-l-2 px-3 py-2 text-sm transition-colors ${cls}">
                ${topic.label}
              </a>
            </li>`;
        }).join("")}
      </ul>`;
  }

  function init(options) {
    const topicId = options?.topicId || "index";
    const title = options?.title || "Help";
    const helpHref = options?.helpHref || "/help/";

    if (global.HubLayout) {
      global.HubLayout.init({
        active: "help",
        title,
        helpHref,
        showApi: true,
      });
    }
    renderWikiNav(topicId);
  }

  global.HelpLayout = { TOPICS, init, renderWikiNav };
})(window);
