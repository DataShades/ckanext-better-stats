declare const echarts: any;
declare const bootstrap: any;

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

    constructor(container: HTMLElement) {
        this.container = container;
        this.charts = {};
        this.currentVizTypes = {};
        this.loadTimes = {};
        this.defaultViz = "chart";
        this.init();
    }

    init() {
        this._bindEvents();
        this._startCacheAgeTimer();
        this.loadAllMetrics();
        this.container.querySelectorAll("[data-bs-toggle='tooltip']").forEach(
            (el) => new bootstrap.Tooltip(el)
        );
        ckan.pubsub.publish("bstats:manager-ready", this);
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

        // Refresh all
        document.getElementById("refresh-all")?.addEventListener("click", () => {
            this.refreshAllMetrics();
        });

        // Retry on error
        this.container.addEventListener("click", (e) => {
            const btn = (e.target as Element).closest(".retry-btn") as HTMLElement | null;
            if (btn) this.refreshMetric(btn.dataset.metric!);
        });
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

    _isDark() {
        return this.container.dataset.bstatsTheme === "dark";
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
