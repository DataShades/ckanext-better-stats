ckan.module("bstats-filter", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);
            new BetterStatsFilter(this.el[0] as HTMLElement);
        },
    };
});

class BetterStatsFilter {
    private container: HTMLElement;
    private activeGroup = "all";

    constructor(container: HTMLElement) {
        this.container = container;
        this._bindEvents();
    }

    _bindEvents() {
        document.getElementById("bstats-metric-search")?.addEventListener("input", () => this._updateVisibility());

        document.getElementById("bstats-group-filter")?.addEventListener("click", (e) => {
            const pill = (e.target as Element).closest(".bstats-group-pill") as HTMLElement | null;
            if (pill) this._filterByGroup(pill.dataset.group!);
        });

        this.container.addEventListener("click", (e) => {
            const toggle = (e.target as Element).closest(".bstats-group-toggle") as HTMLElement | null;
            if (toggle) this._toggleSection(toggle.dataset.group!);
        });
    }

    _filterByGroup(groupName: string) {
        this.activeGroup = groupName;
        document.querySelectorAll<HTMLElement>(".bstats-group-pill").forEach((p) => {
            p.classList.toggle("active", p.dataset.group === groupName);
        });
        const searchInput = document.getElementById("bstats-metric-search") as HTMLInputElement | null;
        if (searchInput) searchInput.value = "";
        this._updateVisibility();
    }

    _toggleSection(groupName: string) {
        const grid = document.getElementById(`bstats-grid-${groupName}`);
        const toggleBtn = this.container.querySelector<HTMLElement>(
            `.bstats-group-toggle[data-group="${groupName}"]`
        );
        if (!grid || !toggleBtn) return;

        const isCollapsed = grid.classList.toggle("is-collapsed");
        toggleBtn.setAttribute("aria-expanded", String(!isCollapsed));
        toggleBtn.querySelector(".bstats-group-chevron")?.classList.toggle("is-collapsed", isCollapsed);
    }

    _updateVisibility() {
        const searchInput = document.getElementById("bstats-metric-search") as HTMLInputElement | null;
        const q = searchInput?.value.toLowerCase() || "";
        let anyVisible = false;

        this.container.querySelectorAll<HTMLElement>(".bstats-group-section").forEach((section) => {
            const groupName = section.dataset.group!;
            const groupMatch = this.activeGroup === "all" || this.activeGroup === groupName;

            if (!groupMatch) {
                section.style.display = "none";
                return;
            }

            let sectionVisible = 0;
            section.querySelectorAll<HTMLElement>(".metric-container").forEach((c) => {
                const name = (c.dataset.metric || "").toLowerCase();
                const title = (c.querySelector(".metric-title")?.textContent || "").toLowerCase();
                const description = (c.dataset.description || "").toLowerCase();
                const show = !q || name.includes(q) || title.includes(q) || description.includes(q);
                c.style.display = show ? "" : "none";
                if (show) sectionVisible++;
            });

            // Always keep favorites section visible (empty/anon state placeholder).
            const isFavSection = groupName === "favorites";
            const showSection = isFavSection || sectionVisible > 0;
            section.style.display = showSection ? "" : "none";
            if (sectionVisible > 0) anyVisible = true;
        });

        const noResults = document.getElementById("bstats-no-results");
        if (noResults) noResults.style.display = (q && !anyVisible) ? "block" : "none";
    }
}
