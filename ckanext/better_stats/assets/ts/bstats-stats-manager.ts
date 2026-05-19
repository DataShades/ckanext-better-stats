import { VIZ, VizType } from "./bstats-types";

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
    private currentVizTypes: Record<string, VizType>;
    private loadTimes: Record<string, number>;
    private defaultViz: VizType;

    constructor(container: HTMLElement) {
        this.container = container;
        this.charts = {};
        this.currentVizTypes = {};
        this.loadTimes = {};
        this.defaultViz = VIZ.CHART;
        this.init();
    }

    init() {
        this._bindEvents();
        this._startCacheAgeTimer();
        this.loadAllMetrics();
        this.container.querySelectorAll("[data-bs-toggle='tooltip']").forEach(
            (el) => new bootstrap.Tooltip(el)
        );
        // Expose the instance so modules that init after us (and thus miss
        // the pub-sub event) can still pick it up synchronously.
        (window as any).bstatsManager = this;
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

        const vizOverride = this._toVizType(new URLSearchParams(window.location.search).get("viz"));

        if (vizOverride) {
            for (const c of containers) {
                await this.loadMetric(c.dataset.metric!, vizOverride, false, c);
            }
        } else {
            await this._loadBatch(containers);
        }
    }

    _toVizType(s: string | null | undefined): VizType | undefined {
        const values = Object.values(VIZ) as readonly string[];
        return s && values.includes(s) ? (s as VizType) : undefined;
    }

    // Load a single metric into a specific container (or auto-detect the first matching container).
    async loadMetric(metricName: string, vizType = this.defaultViz, refresh = false, container?: HTMLElement) {
        const c = container
            ?? this.container.querySelector<HTMLElement>(`.metric-container[data-content-id="${metricName}"]`)
            ?? this.container.querySelector<HTMLElement>(`.metric-container[data-metric="${metricName}"]`);
        const contentId = c?.dataset.contentId ?? metricName;
        const el = document.getElementById(`metric-${contentId}`);
        if (!el) return;

        this._disposeChartById(contentId);

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
            el.replaceChildren(this._errorEl(metricName, (err as Error).message));
        }
    }

    renderMetric(container: HTMLElement, data: any, vizType: VizType, contentId?: string) {
        const id = contentId ?? data.name;
        switch (vizType) {
            case VIZ.CHART: this.renderChart(container, data, id); break;
            case VIZ.TABLE: this.renderTable(container, data); break;
            case VIZ.CARD: this.renderCard(container, data); break;
            case VIZ.PROGRESS: this.renderProgress(container, data); break;
        }
    }

    renderChart(container: HTMLElement, data: any, contentId?: string) {
        const id = contentId ?? data.name;
        const chartData = data.data;

        if (this._isChartEmpty(chartData)) {
            container.appendChild(this._emptyEl());
            return;
        }

        this._disposeChartById(id);

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

            const row = this._el("div", { className: "metric-progress-item" });
            const header = this._el("div", { className: "d-flex justify-content-between mb-1" });
            header.appendChild(this._el("span", { textContent: String(item.label ?? "") }));
            header.appendChild(this._el("span", {
                className: "text-muted",
                textContent: `${item.value} / ${item.max} ${item.unit}`,
            }));

            const bar = this._el("div", { className: "progress" });
            const fill = this._el("div", { className: `progress-bar bg-${color}` });
            fill.style.width = `${pct}%`;
            fill.setAttribute("role", "progressbar");
            fill.setAttribute("aria-valuenow", String(pct));
            fill.setAttribute("aria-valuemin", "0");
            fill.setAttribute("aria-valuemax", "100");
            bar.appendChild(fill);

            row.append(header, bar);
            wrapper.appendChild(row);
        });
        container.appendChild(wrapper);
    }

    renderCard(container: HTMLElement, data: any) {
        const cardData = data.data;
        if (!cardData) {
            container.innerHTML = '<div class="alert alert-info">Card view not available</div>';
            return;
        }
        const div = this._el("div", { className: "metric-card-display" });
        div.appendChild(this._el("div", {
            className: "metric-card-value",
            textContent: this.formatNumber(cardData.value),
        }));
        div.appendChild(this._el("div", {
            className: "metric-card-label",
            textContent: String(cardData.label ?? ""),
        }));
        container.appendChild(div);
    }

    async switchVisualization(metricName: string, vizType: string, pill: HTMLElement) {
        const card = pill.closest<HTMLElement>(".metric-container");
        // Update pills only within this specific card
        card?.querySelectorAll<HTMLElement>(`.viz-pill[data-metric="${metricName}"]`).forEach((p) =>
            p.classList.remove("active")
        );
        pill.classList.add("active");
        await this.loadMetric(metricName, this._toVizType(vizType), false, card ?? undefined);
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
                        el.replaceChildren(this._errorEl(metricName, errorMsg || "Not available"));
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
                    await this.loadMetric(name, this._toVizType(c.dataset.defaultViz), refresh, c);
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
                template.replace(/\{(\w+)\}/g, (_match, key) => {
                    const value =
                        key === "b" ? params.name :
                        key === "c" ? params.value :
                        params.data?.[key];
                    return this._escapeHtml(value ?? "");
                });
            delete chartData.tooltip._htmlTooltip;
        }

        const chart = echarts.init(holder, this._isDark() ? "dark" : "default");
        chart.setOption(chartData);
        chart._chartOptions = chartData;

        const observer = new ResizeObserver(() => chart.resize());
        observer.observe(holder);
        chart._bstatsResizeObserver = observer;

        return chart;
    }

    _disposeChart(chart: any) {
        chart?._bstatsResizeObserver?.disconnect();
        chart?.dispose();
    }

    _disposeChartById(id: string) {
        const existing = this.charts[id];
        if (!existing) return;
        (Array.isArray(existing) ? existing : [existing]).forEach((c) => this._disposeChart(c));
        delete this.charts[id];
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
        const div = this._el("div", { className: "metric-empty" });
        div.appendChild(this._el("i", { className: "fa fa-inbox metric-empty-icon" }));
        div.appendChild(this._el("p", { textContent: "No data available" }));
        return div;
    }

    _errorEl(metricName: string, message: string): HTMLElement {
        const div = this._el("div", { className: "metric-error" });
        div.appendChild(this._el("i", { className: "fa fa-exclamation-triangle metric-error-icon" }));
        div.appendChild(this._el("p", {
            className: "mb-1",
            textContent: message || "Could not load metric",
        }));
        const btn = this._el("button", {
            className: "btn btn-sm btn-outline-secondary retry-btn",
            textContent: "Retry",
        });
        btn.dataset.metric = metricName;
        div.appendChild(btn);
        return div;
    }

    _el<K extends keyof HTMLElementTagNameMap>(tag: K, props: Partial<HTMLElementTagNameMap[K]> = {}): HTMLElementTagNameMap[K] {
        return Object.assign(document.createElement(tag), props);
    }

    _escapeHtml(value: unknown): string {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    formatNumber(num: number) {
        if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
        if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
        return String(num);
    }
}
