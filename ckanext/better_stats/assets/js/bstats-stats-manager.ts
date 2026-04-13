declare const ckan: any;
declare const echarts: any;
declare const bootstrap: any;
declare const snapdom: any;

ckan.module("bstats-stats-manager", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);
            new BetterStatsManager(this.el[0]);
        },
    };
});


class BetterStatsManager {
    private container: HTMLElement;
    private charts: Record<string, any>;
    private currentVizTypes: Record<string, string>;
    private loadTimes: Record<string, number>;
    private defaultViz: string;
    private _fullscreenChart: any;
    private _pendingFullscreen: string | null;
    private _pendingFullscreenContentId: string | null;
    private _activeGroup: string;

    constructor(container: HTMLElement) {
        this.container = container;
        this.charts = {};
        this.currentVizTypes = {};
        this.loadTimes = {};
        this.defaultViz = "chart";
        this._fullscreenChart = null;
        this._pendingFullscreen = null;
        this._pendingFullscreenContentId = null;
        this._activeGroup = "all";
        this.init();
    }

    init() {
        this._bindEvents();
        this._initTheme();
        this._startCacheAgeTimer();
        this.loadAllMetrics();
        this.container.querySelectorAll("[data-bs-toggle='tooltip']").forEach(
            (el) => new bootstrap.Tooltip(el)
        );
    }

    _bindEvents() {
        // Pill viz switcher
        this.container.addEventListener("click", (e) => {
            const pill = (e.target as Element).closest(".viz-pill") as HTMLElement | null;
            if (pill && !pill.classList.contains("active")) {
                this.switchVisualization(pill.dataset.metric!, pill.dataset.type!, pill);
            }
        });

        // Refresh button — pass the card container so the right instance is refreshed
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".refresh-metric") as HTMLElement | null;
            if (btn) {
                const card = btn.closest<HTMLElement>(".metric-container") ?? undefined;
                this.refreshMetric(btn.dataset.metric!, card);
            }
        });

        // Share — copy standalone link to clipboard
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".share-metric") as HTMLElement | null;
            if (btn) this.shareMetric(btn.dataset.metric!, btn);
        });

        // Favorite toggle
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".favorite-btn") as HTMLElement | null;
            if (btn) this._toggleFavorite(btn.dataset.metric!, btn);
        });

        // Refresh all
        document.getElementById("refresh-all")?.addEventListener("click", () => {
            this.refreshAllMetrics();
        });

        // Dark mode toggle
        document.getElementById("bstats-theme-toggle")?.addEventListener("click", () => {
            this._toggleTheme();
        });

        // Export CSV / JSON
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".export-btn") as HTMLElement | null;
            if (btn) {
                e.preventDefault();
                this.exportMetric(btn.dataset.metric!, btn.dataset.format!);
            }
        });

        // Export PNG
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".export-image-btn") as HTMLElement | null;
            if (btn) {
                e.preventDefault();
                this.exportImage(btn.dataset.metric!);
            }
        });

        // Embed modal
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".bstats-embed-btn") as HTMLElement | null;
            if (btn) {
                e.preventDefault();
                const card = btn.closest<HTMLElement>(".metric-container");
                const contentId = card?.dataset.contentId ?? btn.dataset.metric!;
                this.openEmbedModal(btn.dataset.metric!, contentId);
            }
        });

        // Copy embed code
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".bstats-copy-embed");
            if (btn) this.copyEmbedCode(e);
        });

        // Retry on error
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".retry-btn") as HTMLElement | null;
            if (btn) this.refreshMetric(btn.dataset.metric!);
        });

        // Expand → fullscreen modal
        const fsModal = document.getElementById("bstats-fullscreen-modal");
        fsModal?.addEventListener("show.bs.modal", (e) => {
            const trigger = (e as any).relatedTarget as HTMLElement | null;

            if (trigger) {
                this._pendingFullscreen = trigger.dataset.metric!;
                const card = trigger.closest<HTMLElement>(".metric-container");
                this._pendingFullscreenContentId = card?.dataset.contentId ?? trigger.dataset.metric!;
            }

            // Show skeleton immediately while the modal animates open
            const contentEl = document.getElementById("bstats-fullscreen-content");
            if (contentEl) contentEl.innerHTML = this._skeletonHTML();
        });

        // Initialise the chart only after the modal is fully visible so ECharts
        // measures the correct container dimensions.
        fsModal?.addEventListener("shown.bs.modal", () => this._openFullscreen());
        fsModal?.addEventListener("hidden.bs.modal", () => this._closeFullscreen());

        // Search / filter
        document.getElementById("bstats-metric-search")?.addEventListener("input", () => {
            this._updateVisibility();
        });

        // Group filter pills
        document.getElementById("bstats-group-filter")?.addEventListener("click", (e) => {
            const pill = (e.target as Element).closest(".bstats-group-pill") as HTMLElement | null;
            if (pill) this._filterByGroup(pill.dataset.group!);
        });

        // Group section collapse / expand
        this.container.addEventListener("click", (e) => {
            const toggle = (e.target as Element).closest(".bstats-group-toggle") as HTMLElement | null;
            if (toggle) this._toggleSection(toggle.dataset.group!);
        });
    }

    _filterByGroup(groupName: string) {
        this._activeGroup = groupName;
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
            const groupMatch = this._activeGroup === "all" || this._activeGroup === groupName;

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

            // Always keep favorites section visible (even with empty/anon state)
            const isFavSection = groupName === "favorites";
            const showSection = isFavSection || sectionVisible > 0;
            section.style.display = showSection ? "" : "none";
            if (showSection) anyVisible = true;
        });

        const noResults = document.getElementById("bstats-no-results");
        if (noResults) noResults.style.display = anyVisible ? "none" : "block";
    }

    async loadAllMetrics() {
        const containers = [...this.container.querySelectorAll<HTMLElement>(".metric-container")];
        if (!containers.length) return;

        const vizOverride = new URLSearchParams(window.location.search).get("viz");

        if (vizOverride) {
            for (const c of containers) {
                await this.loadMetric(c.dataset.metric!, vizOverride, false, c);
            }
        } else {
            await this._loadBatch(containers);
        }
    }

    // Load a single metric into a specific container (or auto-detect the first matching container).
    async loadMetric(metricName: string, vizType = this.defaultViz, refresh = false, container?: HTMLElement) {
        const c = container
            ?? this.container.querySelector<HTMLElement>(`.metric-container[data-content-id="${metricName}"]`)
            ?? this.container.querySelector<HTMLElement>(`.metric-container[data-metric="${metricName}"]`);
        const contentId = c?.dataset.contentId ?? metricName;
        const el = document.getElementById(`metric-${contentId}`);
        if (!el) return;

        el.innerHTML = this._skeletonHTML();

        try {
            const url = ckan.url(`/better_stats/metric/${metricName}?type=${vizType}${refresh ? "&refresh=true" : ""}`);
            const resp = await fetch(url);
            const data = await resp.json();

            if (data.error) throw new Error(data.error);

            const servedType = data.type || vizType;
            el.innerHTML = "";
            this.renderMetric(el, data, servedType, contentId);
            this.currentVizTypes[contentId] = servedType;
            this._updatePills(metricName, servedType, c ?? undefined);
            this.loadTimes[metricName] = Date.now();
            this._updateCacheAge(metricName);
        } catch (err) {
            el.innerHTML = this._errorHTML(metricName, (err as Error).message);
        }
    }

    renderMetric(container: HTMLElement, data: any, vizType: string, contentId?: string) {
        const id = contentId ?? data.name;
        switch (vizType) {
            case "chart": this.renderChart(container, data, id); break;
            case "table": this.renderTable(container, data); break;
            case "card": this.renderCard(container, data); break;
            case "progress": this.renderProgress(container, data); break;
        }
    }

    renderChart(container: HTMLElement, data: any, contentId?: string) {
        const id = contentId ?? data.name;
        const chartData = data.data;

        if (this._isChartEmpty(chartData)) {
            container.appendChild(this._emptyEl());
            return;
        }

        const existing = this.charts[id];
        if (existing) {
            (Array.isArray(existing) ? existing : [existing]).forEach((c) => c.dispose());
            delete this.charts[id];
        }

        if (chartData.type === "multi") {
            const wrapper = this._el("div", { className: "metric-chart-multi" });
            container.appendChild(wrapper);

            this.charts[id] = chartData.charts.map((sub: any) => {
                const item = this._el("div", { className: "metric-chart-item" });
                wrapper.appendChild(item);
                return this._createChart(item, sub);
            });
        } else {
            this.charts[id] = this._createChart(container, chartData);
        }
    }

    renderTable(container: HTMLElement, data: any) {
        const tableData = data.data;

        if (!tableData?.rows?.length) {
            container.appendChild(this._emptyEl());
            return;
        }

        const wrapper = this._el("div", { className: "metric-table-wrapper" });
        const table = this._el("table", { className: "metric-table" });
        const thead = this._el("thead");
        const headerRow = this._el("tr");

        (tableData.headers || []).forEach((h: string) => {
            headerRow.appendChild(this._el("th", { textContent: h }));
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = this._el("tbody");
        (tableData.rows || []).forEach((row: any[]) => {
            const tr = this._el("tr");
            row.forEach((cell) => {
                const td = this._el("td");

                if (cell !== null && typeof cell === "object" && cell.url) {
                    const a = this._el("a", { textContent: cell.text ?? cell.url, href: cell.url });
                    td.appendChild(a);
                } else {
                    td.textContent = cell;
                }

                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        wrapper.appendChild(table);
        container.appendChild(wrapper);
    }

    renderProgress(container: HTMLElement, data: any) {
        const items = data.data?.items;
        if (!items?.length) {
            container.innerHTML = '<div class="alert alert-info">No data available</div>';
            return;
        }
        const wrapper = this._el("div", { className: "metric-progress" });
        items.forEach((item: any) => {
            const pct = Math.min(100, Math.round((item.value / item.max) * 100));
            const color = pct > 90 ? "danger" : pct > 70 ? "warning" : "success";
            wrapper.insertAdjacentHTML(
                "beforeend",
                `<div class="metric-progress-item">
                    <div class="d-flex justify-content-between mb-1">
                        <span>${item.label}</span>
                        <span class="text-muted">${item.value} / ${item.max} ${item.unit}</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar bg-${color}" style="width:${pct}%"
                             role="progressbar" aria-valuenow="${pct}"
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>`
            );
        });
        container.appendChild(wrapper);
    }

    renderCard(container: HTMLElement, data: any) {
        const cardData = data.data;
        if (!cardData) {
            container.innerHTML = '<div class="alert alert-info">Card view not available</div>';
            return;
        }
        const div = this._el("div", {
            className: "metric-card-display",
            innerHTML: `<div class="metric-card-value">${this.formatNumber(cardData.value)}</div>` +
                       `<div class="metric-card-label">${cardData.label}</div>`,
        });
        container.appendChild(div);
    }

    async switchVisualization(metricName: string, vizType: string, pill: HTMLElement) {
        const card = pill.closest<HTMLElement>(".metric-container");
        // Update pills only within this specific card
        card?.querySelectorAll<HTMLElement>(`.viz-pill[data-metric="${metricName}"]`).forEach((p) =>
            p.classList.remove("active")
        );
        pill.classList.add("active");
        await this.loadMetric(metricName, vizType, false, card ?? undefined);
    }

    async refreshMetric(metricName: string, container?: HTMLElement) {
        const contentId = container?.dataset.contentId ?? metricName;
        await this.loadMetric(metricName, this.currentVizTypes[contentId] || this.defaultViz, true, container);
    }

    async refreshAllMetrics() {
        const containers = [...this.container.querySelectorAll<HTMLElement>(".metric-container")];
        if (containers.length) await this._loadBatch(containers, true);
    }

    shareMetric(metricName: string, btn: HTMLElement) {
        const card = btn.closest<HTMLElement>(".metric-container");
        const contentId = card?.dataset.contentId ?? metricName;
        const vizType = this.currentVizTypes[contentId] || this.defaultViz;
        const url = ckan.url(`/better_stats/embed/${metricName}?viz=${encodeURIComponent(vizType)}`);
        navigator.clipboard.writeText(url).then(() => {
            const icon = btn.querySelector("i") as HTMLElement | null;
            if (icon) {
                icon.className = "fa fa-check fa-fw";
                setTimeout(() => { icon.className = "fa fa-link fa-fw"; }, 2000);
            }
        });
    }

    async _loadBatch(containers: HTMLElement[], refresh = false) {
        // Deduplicate by metric name; track all containers per name
        const nameToContainers = new Map<string, HTMLElement[]>();
        containers.forEach((c) => {
            const name = c.dataset.metric!;
            const bucket = nameToContainers.get(name) ?? [];
            bucket.push(c);
            nameToContainers.set(name, bucket);
        });

        const uniqueNames = [...nameToContainers.keys()];

        if (refresh) {
            containers.forEach((c) => {
                const contentId = c.dataset.contentId ?? c.dataset.metric!;
                const el = document.getElementById(`metric-${contentId}`);
                if (el) el.innerHTML = this._skeletonHTML();
            });
        }

        const url = ckan.url(
            `/better_stats/metrics?names=${encodeURIComponent(uniqueNames.join(","))}${refresh ? "&refresh=true" : ""}`
        );

        try {
            const resp = await fetch(url);
            const batch = await resp.json();

            for (const [metricName, metricContainers] of nameToContainers) {
                const data = batch.metrics?.[metricName];
                const errorMsg = batch.errors?.[metricName];

                for (const c of metricContainers) {
                    const contentId = c.dataset.contentId ?? metricName;
                    const el = document.getElementById(`metric-${contentId}`);
                    if (!el) continue;

                    if (!data) {
                        el.innerHTML = this._errorHTML(metricName, errorMsg || "Not available");
                        continue;
                    }

                    el.innerHTML = "";
                    this.renderMetric(el, data, data.type, contentId);
                    this.currentVizTypes[contentId] = data.type;
                    this._updatePills(metricName, data.type, c);
                }

                if (data) {
                    this.loadTimes[metricName] = Date.now();
                    this._updateCacheAge(metricName);
                }
            }
        } catch (err) {
            // Batch failed — fall back to individual loads
            for (const [name, cs] of nameToContainers) {
                for (const c of cs) {
                    await this.loadMetric(name, c.dataset.defaultViz || this.defaultViz, refresh, c);
                }
            }
        }
    }

    exportMetric(metricName: string, format: string) {
        window.open(ckan.url(`/better_stats/export/${metricName}?format=${format}`, "_blank"));
    }

    async exportImage(metricName: string) {
        // Export from the first non-fav instance
        const card = this.container.querySelector<HTMLElement>(
            `.metric-container[data-metric="${metricName}"]:not([data-content-id^="fav-"])`
        ) ?? this.container.querySelector<HTMLElement>(`.metric-container[data-metric="${metricName}"]`);
        const contentId = card?.dataset.contentId ?? metricName;
        const content = document.getElementById(`metric-${contentId}`);
        if (!content) return;
        try {
            const result = await snapdom(content, { scale: 2 });
            await result.download({
                format: "png",
                filename: `metric-${metricName}-${new Date().toISOString()}.png`,
                backgroundColor: "#ffffff",
            });
        } catch (err) {
            console.error("PNG export failed:", err);
        }
    }

    openEmbedModal(metricName: string, contentId = metricName) {
        const vizType = this.currentVizTypes[contentId] || this.defaultViz;
        const embedUrl = ckan.url(`/better_stats/embed/${metricName}?viz=${encodeURIComponent(vizType)}`);
        const code = `<iframe src="${embedUrl}" width="600" height="400" frameborder="0" style="border:1px solid #e2e8f0;border-radius:8px"></iframe>`;

        const textarea = document.getElementById(`embedCode-${metricName}`) as HTMLTextAreaElement | null;
        if (textarea) textarea.value = code;

        const preview = document.getElementById(`embedPreview-${metricName}`) as HTMLIFrameElement | null;
        if (preview) preview.src = embedUrl;
    }

    copyEmbedCode(e: Event) {
        const btn = (e.target as Element).closest(".bstats-copy-embed") as HTMLElement | null;
        if (!btn) return;
        const textarea = document.getElementById(btn.dataset.target!) as HTMLTextAreaElement | null;
        if (!textarea) return;
        textarea.select();
        navigator.clipboard.writeText(textarea.value).then(() => {
            const icon = btn.querySelector("i") as HTMLElement | null;
            if (icon) {
                icon.className = "fa fa-check text-success";
                setTimeout(() => { icon.className = "fa fa-clipboard"; }, 2000);
            }
        }).catch(() => document.execCommand("copy"));
    }

    // ── Favorites ──────────────────────────────────────────────────────────────

    _getCsrfToken(): string | null {
        const fieldName = document.querySelector<HTMLMetaElement>('meta[name="csrf_field_name"]')?.content;
        if (!fieldName) return null;
        return document.querySelector<HTMLMetaElement>(`meta[name="${fieldName}"]`)?.content ?? null;
    }

    async _toggleFavorite(metricName: string, btn: HTMLElement) {
        const csrfToken = this._getCsrfToken();
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (csrfToken) headers["X-CSRFToken"] = csrfToken;

        try {
            const resp = await fetch(ckan.url(`/better_stats/favorites/toggle/${metricName}`), {
                method: "POST",
                headers,
            });
            const data = await resp.json();
            if (data.error) return;

            this._setStarState(metricName, data.is_favorite);

            if (data.is_favorite && data.card_html) {
                this._addFavCard(data.card_html, metricName);
            } else if (!data.is_favorite) {
                this._removeFavCard(metricName);
            }
        } catch (err) {
            console.error("Failed to toggle favorite:", err);
        }
    }

    _setStarState(metricName: string, isFavorite: boolean) {
        this.container.querySelectorAll<HTMLElement>(`.favorite-btn[data-metric="${metricName}"]`).forEach((btn) => {
            const icon = btn.querySelector("i");
            if (icon) icon.className = isFavorite ? "fa-solid fa-star fav-active" : "fa-regular fa-star";
            btn.dataset.favorited = isFavorite ? "true" : "false";
            btn.title = isFavorite ? "Remove from favorites" : "Add to favorites";
        });
    }

    _addFavCard(cardHtml: string, metricName: string) {
        const grid = document.getElementById("bstats-grid-favorites");
        if (!grid) return;

        grid.querySelector(".bstats-fav-empty")?.remove();

        const tmp = this._el("div", { innerHTML: cardHtml });
        const newCard = tmp.firstElementChild as HTMLElement | null;
        if (!newCard) return;
        grid.appendChild(newCard);

        newCard.querySelectorAll("[data-bs-toggle='tooltip']").forEach((el) => new bootstrap.Tooltip(el));

        const vizType = this.currentVizTypes[metricName] || this.defaultViz;
        this.loadMetric(metricName, vizType, false, newCard);
        this._updateFavCount(grid);
    }

    _removeFavCard(metricName: string) {
        const grid = document.getElementById("bstats-grid-favorites");
        if (!grid) return;

        const card = grid.querySelector<HTMLElement>(`.metric-container[data-metric="${metricName}"]`);
        if (!card) return;

        const contentId = card.dataset.contentId ?? `fav-${metricName}`;
        const chart = this.charts[contentId];
        if (chart) {
            (Array.isArray(chart) ? chart : [chart]).forEach((c) => c.dispose());
            delete this.charts[contentId];
        }
        card.remove();
        this._updateFavCount(grid);

        if (!grid.querySelector(".metric-container")) {
            grid.insertAdjacentHTML(
                "beforeend",
                `<div class="bstats-fav-empty col-span-full">` +
                `<p class="mb-0">No favorites yet \u2014 click the <i class="fa-regular fa-star"></i> on any metric to add it here.</p>` +
                `</div>`
            );
        }
    }

    _updateFavCount(grid: HTMLElement) {
        const count = grid.querySelectorAll(".metric-container").length;
        const badge = this.container.querySelector(
            `.bstats-group-toggle[data-group="favorites"] .bstats-group-count`
        );
        if (badge) badge.textContent = String(count);
    }

    async _openFullscreen() {
        const metricName = this._pendingFullscreen;
        if (!metricName) return;

        const titleEl = document.getElementById("bstats-fullscreen-title");
        const contentEl = document.getElementById("bstats-fullscreen-content");
        if (!contentEl) return;

        const contentId = this._pendingFullscreenContentId ?? metricName;
        const vizType = this.currentVizTypes[contentId] || this.defaultViz;

        try {
            const resp = await fetch(ckan.url(`/better_stats/metric/${metricName}?type=${vizType}`));
            const data = await resp.json();
            if (data.error) throw new Error(data.error);

            if (titleEl) titleEl.textContent = data.title;
            contentEl.innerHTML = "";

            if (vizType === "chart") {
                this._fullscreenChart = this._createChart(contentEl, data.data);
            } else {
                this.renderMetric(contentEl, data, vizType);
            }
        } catch (err) {
            contentEl.innerHTML = this._errorHTML(metricName, (err as Error).message);
        }
    }

    _closeFullscreen() {
        if (this._fullscreenChart) {
            this._fullscreenChart.dispose();
            this._fullscreenChart = null;
        }
        const contentEl = document.getElementById("bstats-fullscreen-content");
        if (contentEl) contentEl.innerHTML = "";
        this._pendingFullscreen = null;
        this._pendingFullscreenContentId = null;
    }

    _isDark() {
        return this.container.dataset.bstatsTheme === "dark";
    }

    _initTheme() {
        if (localStorage.getItem("bstats-theme") === "dark") {
            this.container.dataset.bstatsTheme = "dark";
            this._updateToggleIcon(true);
        }
    }

    _toggleTheme() {
        const dark = !this._isDark();
        this.container.dataset.bstatsTheme = dark ? "dark" : "";
        localStorage.setItem("bstats-theme", dark ? "dark" : "");
        this._updateToggleIcon(dark);
        this._updateChartsTheme();
    }

    _updateToggleIcon(dark: boolean) {
        const icon = document.querySelector("#bstats-theme-toggle i") as HTMLElement | null;
        if (icon) icon.className = dark ? "fa fa-sun" : "fa fa-moon";
    }

    _updateChartsTheme() {
        const dark = this._isDark();
        Object.values(this.charts).forEach((entry) => {
            (Array.isArray(entry) ? entry : [entry]).forEach((chart) => {
                chart.setTheme(dark ? "dark" : {});
                chart.setOption(chart._chartOptions || {});
            });
        });
    }

    _startCacheAgeTimer() {
        setInterval(() => {
            Object.keys(this.loadTimes).forEach((name) => this._updateCacheAge(name));
        }, 60000);
    }

    _updateCacheAge(metricName: string) {
        const elements = this.container.querySelectorAll(`.metric-cache-age[data-metric="${metricName}"]`);
        if (!elements.length || !this.loadTimes[metricName]) return;
        const secs = Math.floor((Date.now() - this.loadTimes[metricName]) / 1000);
        const text =
            secs < 10 ? "Updated Just now" :
            secs < 3600 ? `Updated ${Math.floor(secs / 60) || 1}m ago` :
            `Updated ${Math.floor(secs / 3600)}h ago`;
        elements.forEach((el) => { el.textContent = text; });
    }

    _createChart(container: HTMLElement, chartData: any) {
        const holder = this._el("div", { className: "metric-chart" });
        container.appendChild(holder);

        if (chartData.tooltip?._htmlTooltip) {
            const template = chartData.tooltip.formatter as string;
            chartData.tooltip.formatter = (params: any) =>
                template
                    .replace(/\{b\}/g, params.name ?? "")
                    .replace(/\{c\}/g, params.value ?? "");
            delete chartData.tooltip._htmlTooltip;
        }

        const chart = echarts.init(holder, this._isDark() ? "dark" : "default");
        chart.setOption(chartData);
        chart._chartOptions = chartData;
        window.addEventListener("resize", () => chart.resize());

        return chart;
    }

    _updatePills(metricName: string, vizType: string, card?: HTMLElement) {
        const scope: HTMLElement = card ?? this.container;
        scope.querySelectorAll<HTMLElement>(`.viz-pill[data-metric="${metricName}"]`).forEach((p) => {
            p.classList.toggle("active", p.dataset.type === vizType);
        });
    }

    _skeletonHTML() {
        return (
            '<div class="metric-skeleton">' +
            '  <div class="placeholder col-12"></div>' +
            "</div>"
        );
    }

    _isChartEmpty(chartData: any): boolean {
        if (!chartData) return true;
        if (chartData.type === "multi") {
            return !chartData.charts?.length ||
                chartData.charts.every((c: any) => this._isChartEmpty(c));
        }
        const series: any[] = chartData.series || [];
        if (!series.length) return true;
        return series.every((s: any) => !s.data || s.data.length === 0);
    }

    _emptyEl(): HTMLElement {
        return this._el("div", {
            className: "metric-empty",
            innerHTML:
                '<i class="fa fa-inbox metric-empty-icon"></i>' +
                "<p>No data available</p>",
        });
    }

    _errorHTML(metricName: string, message: string) {
        return (
            '<div class="metric-error">' +
            '  <i class="fa fa-exclamation-triangle metric-error-icon"></i>' +
            `  <p class="mb-1">${message || "Could not load metric"}</p>` +
            `  <button class="btn btn-sm btn-outline-secondary retry-btn" data-metric="${metricName}">Retry</button>` +
            "</div>"
        );
    }

    _el<K extends keyof HTMLElementTagNameMap>(tag: K, props: Partial<HTMLElementTagNameMap[K]> = {}): HTMLElementTagNameMap[K] {
        return Object.assign(document.createElement(tag), props);
    }

    formatNumber(num: number) {
        if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
        if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
        return String(num);
    }
}
