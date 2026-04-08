ckan.module("bstats-stats-manager", function ($) {
    return {
        initialize() {
            $.proxyAll(this, /_/);
            new BetterStatsManager(this.el[0]);
        },
    };
});


class BetterStatsManager {
    constructor(container) {
        this.container = container;
        this.charts = {};
        this.currentVizTypes = {};
        this.loadTimes = {};
        this._fullscreenChart = null;
        this._pendingFullscreen = null;
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
            const pill = e.target.closest(".viz-pill");
            if (pill && !pill.classList.contains("active")) {
                this.switchVisualization(pill.dataset.metric, pill.dataset.type, pill);
            }
        });

        // Refresh (now inside actions dropdown)
        this.container.addEventListener("click", (e) => {
            const btn = e.target.closest(".refresh-metric");
            if (btn) this.refreshMetric(btn.dataset.metric);
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
            const btn = e.target.closest(".export-btn");
            if (btn) {
                e.preventDefault();
                this.exportMetric(btn.dataset.metric, btn.dataset.format);
            }
        });

        // Export PNG
        this.container.addEventListener("click", (e) => {
            const btn = e.target.closest(".export-image-btn");
            if (btn) {
                e.preventDefault();
                this.exportImage(btn.dataset.metric);
            }
        });

        // Embed modal
        this.container.addEventListener("click", (e) => {
            const btn = e.target.closest(".bstats-embed-btn");
            if (btn) {
                e.preventDefault();
                this.openEmbedModal(btn.dataset.metric);
            }
        });

        // Copy embed code
        this.container.addEventListener("click", (e) => {
            const btn = e.target.closest(".bstats-copy-embed");
            if (btn) this.copyEmbedCode(e);
        });

        // Retry on error
        this.container.addEventListener("click", (e) => {
            const btn = e.target.closest(".retry-btn");
            if (btn) this.refreshMetric(btn.dataset.metric);
        });

        // Expand → fullscreen modal; use relatedTarget so the metric name
        // is available synchronously when show.bs.modal fires.
        const fsModal = document.getElementById("bstats-fullscreen-modal");
        fsModal?.addEventListener("show.bs.modal", (e) => {
            const trigger = e.relatedTarget;
            if (trigger) this._pendingFullscreen = trigger.dataset.metric;
            this._openFullscreen();
        });
        fsModal?.addEventListener("hidden.bs.modal", () => this._closeFullscreen());

        // Search / filter
        document.getElementById("bstats-metric-search")?.addEventListener("input", (e) => {
            const q = e.target.value.toLowerCase();
            let visible = 0;
            this.container.querySelectorAll(".metric-container").forEach((c) => {
                const name = c.dataset.metric.toLowerCase();
                const title = (c.querySelector(".metric-title")?.textContent || "").toLowerCase();
                const description = (c.dataset.description || "").toLowerCase();
                const show = !q || name.includes(q) || title.includes(q) || description.includes(q);
                c.style.display = show ? "" : "none";
                if (show) visible++;
            });
            const noResults = document.getElementById("bstats-no-results");
            if (noResults) noResults.style.display = visible === 0 ? "block" : "none";
        });
    }

    async loadAllMetrics() {
        const containers = [...this.container.querySelectorAll(".metric-container")];
        if (containers.length) await this._loadBatch(containers);
    }

    async loadMetric(metricName, vizType = "chart", refresh = false) {
        const el = document.getElementById(`metric-${metricName}`);
        if (!el) return;

        el.innerHTML = this._skeletonHTML();

        try {
            const url = ckan.url(`/better_stats/metric/${metricName}?type=${vizType}${refresh ? "&refresh=true" : ""}`);
            const resp = await fetch(url);
            const data = await resp.json();

            if (data.error) throw new Error(data.error);

            const servedType = data.type || vizType;
            el.innerHTML = "";
            this.renderMetric(el, data, servedType);
            this.currentVizTypes[metricName] = servedType;
            this._updatePills(metricName, servedType);
            this.loadTimes[metricName] = Date.now();
            this._updateCacheAge(metricName);
        } catch (err) {
            el.innerHTML = this._errorHTML(metricName, err.message);
        }
    }

    renderMetric(container, data, vizType) {
        switch (vizType) {
            case "chart": this.renderChart(container, data); break;
            case "table": this.renderTable(container, data); break;
            case "card": this.renderCard(container, data); break;
            case "progress": this.renderProgress(container, data); break;
        }
    }

    renderChart(container, data) {
        const chartData = data.data;

        const existing = this.charts[data.name];
        if (existing) {
            (Array.isArray(existing) ? existing : [existing]).forEach((c) => c.dispose());
            delete this.charts[data.name];
        }

        if (chartData.type === "multi") {
            const wrapper = this._el("div", { className: "metric-chart-multi" });
            container.appendChild(wrapper);

            this.charts[data.name] = chartData.charts.map((sub) => {
                const item = this._el("div", { className: "metric-chart-item" });
                wrapper.appendChild(item);
                return this._createChart(item, sub);
            });
        } else {
            this.charts[data.name] = this._createChart(container, chartData, data.name);
        }
    }

    renderTable(container, data) {
        const tableData = data.data;

        const wrapper = this._el("div", { className: "metric-table-wrapper" });
        const table = this._el("table", { className: "metric-table" });
        const thead = this._el("thead");
        const headerRow = this._el("tr");

        (tableData.headers || []).forEach((h) => {
            headerRow.appendChild(this._el("th", { textContent: h }));
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = this._el("tbody");
        (tableData.rows || []).forEach((row) => {
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

    renderProgress(container, data) {
        const items = data.data?.items;
        if (!items?.length) {
            container.innerHTML = '<div class="alert alert-info">No data available</div>';
            return;
        }
        const wrapper = this._el("div", { className: "metric-progress" });
        items.forEach((item) => {
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

    renderCard(container, data) {
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

    async switchVisualization(metricName, vizType, pill) {
        const allPills = this.container.querySelectorAll(`.viz-pill[data-metric="${metricName}"]`);
        allPills.forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        await this.loadMetric(metricName, vizType);
    }

    async refreshMetric(metricName) {
        await this.loadMetric(metricName, this.currentVizTypes[metricName] || "chart", true);
    }

    async refreshAllMetrics() {
        const containers = [...this.container.querySelectorAll(".metric-container")];
        if (containers.length) await this._loadBatch(containers, true);
    }

    async _loadBatch(containers, refresh = false) {
        if (refresh) {
            containers.forEach((c) => {
                const el = document.getElementById(`metric-${c.dataset.metric}`);
                if (el) el.innerHTML = this._skeletonHTML();
            });
        }

        const names = containers.map((c) => c.dataset.metric).join(",");
        const url = ckan.url(`/better_stats/metrics?names=${encodeURIComponent(names)}${refresh ? "&refresh=true" : ""}`);

        try {
            const resp = await fetch(url);
            const batch = await resp.json();

            containers.forEach((c) => {
                const metricName = c.dataset.metric;
                const el = document.getElementById(`metric-${metricName}`);
                if (!el) return;

                const data = batch.metrics?.[metricName];
                if (!data) {
                    el.innerHTML = this._errorHTML(metricName, batch.errors?.[metricName] || "Not available");
                    return;
                }

                el.innerHTML = "";
                const vizType = data.type;
                this.renderMetric(el, data, vizType);
                this.currentVizTypes[metricName] = vizType;
                this._updatePills(metricName, vizType);
                this.loadTimes[metricName] = Date.now();
                this._updateCacheAge(metricName);
            });
        } catch (err) {
            // Batch request failed — fall back to individual loads
            for (const c of containers) {
                await this.loadMetric(c.dataset.metric, c.dataset.defaultViz || "chart", refresh);
            }
        }
    }

    exportMetric(metricName, format) {
        window.open(`/better_stats/export/${metricName}?format=${format}`, "_blank");
    }

    async exportImage(metricName) {
        const content = document.getElementById(`metric-${metricName}`);
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

    openEmbedModal(metricName) {
        const vizType = this.currentVizTypes[metricName] || "chart";
        const embedUrl = `${window.location.origin}/better_stats/embed/${metricName}?viz=${encodeURIComponent(vizType)}`;
        const code = `<iframe src="${embedUrl}" width="600" height="400" frameborder="0" style="border:1px solid #e2e8f0;border-radius:8px"></iframe>`;

        const textarea = document.getElementById(`embedCode-${metricName}`);
        if (textarea) textarea.value = code;

        const preview = document.getElementById(`embedPreview-${metricName}`);
        if (preview) preview.src = embedUrl;
    }

    copyEmbedCode(e) {
        const targetId = e.target.closest(".bstats-copy-embed").dataset.target;
        const textarea = document.getElementById(targetId);
        if (!textarea) return;
        textarea.select();
        navigator.clipboard.writeText(textarea.value).then(() => {
            const icon = e.target.closest(".bstats-copy-embed").querySelector("i");
            if (icon) {
                icon.className = "fa fa-check text-success";
                setTimeout(() => { icon.className = "fa fa-clipboard"; }, 2000);
            }
        }).catch(() => document.execCommand("copy"));
    }

    async _openFullscreen() {
        const metricName = this._pendingFullscreen;
        if (!metricName) return;

        const titleEl = document.getElementById("bstats-fullscreen-title");
        const contentEl = document.getElementById("bstats-fullscreen-content");
        if (!contentEl) return;

        contentEl.innerHTML = this._skeletonHTML();

        const vizType = this.currentVizTypes[metricName] || "chart";

        try {
            const resp = await fetch(ckan.url(`/better_stats/metric/${metricName}?type=${vizType}`));
            const data = await resp.json();
            if (data.error) throw new Error(data.error);

            if (titleEl) titleEl.textContent = data.title;
            contentEl.innerHTML = "";

            if (vizType === "chart") {
                this._fullscreenChart = this._createChart(contentEl, data.data, `${metricName}-fs`);
            } else {
                this.renderMetric(contentEl, data, vizType);
            }
        } catch (err) {
            contentEl.innerHTML = this._errorHTML(metricName, err.message);
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

    _updateToggleIcon(dark) {
        const icon = document.querySelector("#bstats-theme-toggle i");
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

    _updateCacheAge(metricName) {
        const el = document.querySelector(`.metric-cache-age[data-metric="${metricName}"]`);
        if (!el || !this.loadTimes[metricName]) return;
        const secs = Math.floor((Date.now() - this.loadTimes[metricName]) / 1000);
        if (secs < 10) el.textContent = "Just updated";
        else if (secs < 3600) el.textContent = `Updated ${Math.floor(secs / 60) || 1}m ago`;
        else el.textContent = `Updated ${Math.floor(secs / 3600)}h ago`;
    }

    _createChart(container, chartData) {
        const holder = this._el("div", { className: "metric-chart" });
        container.appendChild(holder);

        const type = chartData.type || "bar";
        const chart = echarts.init(holder, this._isDark() ? "dark" : "default");

        let option;

        if (type === "pie" || type === "doughnut") {
            option = {
                tooltip: { trigger: "item" },
                legend: { orient: "vertical", left: "left" },
                series: [{
                    type: "pie",
                    radius: type === "doughnut" ? ["40%", "70%"] : "60%",
                    data: (chartData.labels || []).map((label, i) => ({
                        name: String(label),
                        value: chartData.data[i] ?? 0,
                    })),
                }],
            };
        } else if (type === "line") {
            option = {
                tooltip: { trigger: "axis" },
                xAxis: { type: "category", data: chartData.labels || [] },
                yAxis: { type: "value" },
                series: [{ type: "line", data: chartData.data || [], smooth: true }],
            };
        } else if (type === "treemap") {
            option = {
                tooltip: { formatter: "{b}: {c}" },
                series: [{ 
                    type: "treemap", 
                    data: chartData.data || [],
                    label: { show: true, formatter: "{b}" },
                    itemStyle: { borderColor: "#fff" },
                    roam: false,
                }],
            };
        } else {
            const isHorizontal = chartData.options?.indexAxis === "y";
            const barSeries = { type: "bar", data: chartData.data || [], colorBy: "data" };
            option = isHorizontal
                ? {
                    tooltip: { trigger: "axis" },
                    xAxis: { type: "value" },
                    yAxis: { type: "category", data: chartData.labels || [] },
                    series: [barSeries],
                }
                : {
                    tooltip: { trigger: "axis" },
                    xAxis: { type: "category", data: chartData.labels || [] },
                    yAxis: { type: "value" },
                    series: [barSeries],
                };
        }

        chart.setOption(option);
        chart._chartOptions = option;

        return chart;
    }

    _updatePills(metricName, vizType) {
        this.container.querySelectorAll(`.viz-pill[data-metric="${metricName}"]`).forEach((p) => {
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

    _errorHTML(metricName, message) {
        return (
            '<div class="metric-error">' +
            '  <i class="fa fa-exclamation-triangle metric-error-icon"></i>' +
            `  <p class="mb-1">${message || "Could not load metric"}</p>` +
            `  <button class="btn btn-sm btn-outline-secondary retry-btn" data-metric="${metricName}">Retry</button>` +
            "</div>"
        );
    }

    _el(tag, props = {}) {
        return Object.assign(document.createElement(tag), props);
    }

    formatNumber(num) {
        if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
        if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
        return String(num);
    }
}
