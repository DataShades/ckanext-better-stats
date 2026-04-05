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
        this._registerChartBackground();
        this._bindEvents();
        this._startCacheAgeTimer();
        this.loadAllMetrics();
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
                const show = name.includes(q) || title.includes(q);
                c.style.display = show ? "" : "none";
                if (show) visible++;
            });
            const noResults = document.getElementById("bstats-no-results");
            if (noResults) noResults.style.display = visible === 0 ? "block" : "none";
        });
    }

    // ── Loading ────────────────────────────────────────────────

    async loadAllMetrics() {
        const containers = this.container.querySelectorAll(".metric-container");
        for (const c of containers) {
            await this.loadMetric(c.dataset.metric, c.dataset.defaultViz || "chart");
        }
    }

    async loadMetric(metricName, vizType = "chart", refresh = false) {
        const el = document.getElementById(`metric-${metricName}`);
        if (!el) return;

        el.innerHTML = this._skeletonHTML();

        try {
            const url = `/better_stats/metric/${metricName}?type=${vizType}${refresh ? "&refresh=true" : ""}`;
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

    // ── Rendering ─────────────────────────────────────────────

    renderMetric(container, data, vizType) {
        switch (vizType) {
            case "chart": this.renderChart(container, data); break;
            case "table": this.renderTable(container, data); break;
            case "card":  this.renderCard(container, data);  break;
        }
    }

    renderChart(container, data) {
        const chartData = data.data;

        const existing = this.charts[data.name];
        if (existing) {
            (Array.isArray(existing) ? existing : [existing]).forEach((c) => c.destroy());
            delete this.charts[data.name];
        }

        if (chartData.type === "multi") {
            const wrapper = document.createElement("div");
            wrapper.className = "metric-chart-multi";
            container.appendChild(wrapper);
            this.charts[data.name] = chartData.charts.map((sub, i) => {
                const item = document.createElement("div");
                item.className = "metric-chart-item";
                wrapper.appendChild(item);
                return this._createSingleChart(item, sub, `${data.name}-${i}`, sub.title);
            });
        } else {
            this.charts[data.name] = this._createSingleChart(container, chartData, data.name);
        }
    }

    renderTable(container, data) {
        const tableData = data.data;
        const table = document.createElement("table");
        table.className = "metric-table table table-striped";

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        (tableData.headers || []).forEach((h) => {
            const th = document.createElement("th");
            th.textContent = h;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        (tableData.rows || []).forEach((row) => {
            const tr = document.createElement("tr");
            row.forEach((cell) => {
                const td = document.createElement("td");
                td.textContent = cell;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        container.appendChild(table);
    }

    renderCard(container, data) {
        const cardData = data.data;
        if (!cardData) {
            container.innerHTML = '<div class="alert alert-info">Card view not available</div>';
            return;
        }
        const div = document.createElement("div");
        div.className = "metric-card-display";
        div.innerHTML =
            `<div class="metric-card-value">${this.formatNumber(cardData.value)}</div>` +
            `<div class="metric-card-label">${cardData.label}</div>`;
        container.appendChild(div);
    }

    // ── Interactions ───────────────────────────────────────────

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
        for (const c of this.container.querySelectorAll(".metric-container")) {
            await this.refreshMetric(c.dataset.metric);
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

    // ── Fullscreen modal ───────────────────────────────────────

    async _openFullscreen() {
        const metricName = this._pendingFullscreen;
        if (!metricName) return;

        const titleEl = document.getElementById("bstats-fullscreen-title");
        const contentEl = document.getElementById("bstats-fullscreen-content");
        if (!contentEl) return;

        contentEl.innerHTML = this._skeletonHTML();

        const vizType = this.currentVizTypes[metricName] || "chart";

        try {
            const resp = await fetch(`/better_stats/metric/${metricName}?type=${vizType}`);
            const data = await resp.json();
            if (data.error) throw new Error(data.error);

            if (titleEl) titleEl.textContent = data.title;
            contentEl.innerHTML = "";

            if (vizType === "chart") {
                this._fullscreenChart = this._createSingleChart(contentEl, data.data, `${metricName}-fs`);
            } else {
                this.renderMetric(contentEl, data, vizType);
            }
        } catch (err) {
            contentEl.innerHTML = this._errorHTML(metricName, err.message);
        }
    }

    _closeFullscreen() {
        if (this._fullscreenChart) {
            this._fullscreenChart.destroy();
            this._fullscreenChart = null;
        }
        const contentEl = document.getElementById("bstats-fullscreen-content");
        if (contentEl) contentEl.innerHTML = "";
        this._pendingFullscreen = null;
    }

    // ── Cache age ──────────────────────────────────────────────

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

    // ── Chart helpers ──────────────────────────────────────────

    _registerChartBackground() {
        Chart.register({
            id: "chartjs-chart-background",
            beforeDraw: (chart) => {
                const ctx = chart.canvas.getContext("2d");
                ctx.save();
                ctx.globalCompositeOperation = "destination-over";
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, chart.width, chart.height);
                ctx.restore();
            },
        });
    }

    _createSingleChart(container, chartData, key, title = null) {
        if (title) {
            const label = document.createElement("p");
            label.className = "metric-chart-label";
            label.textContent = title;
            container.appendChild(label);
        }
        const canvas = document.createElement("canvas");
        canvas.className = "metric-chart";
        container.appendChild(canvas);

        return new Chart(canvas.getContext("2d"), {
            type: chartData.type || "bar",
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    data: chartData.data || [],
                    backgroundColor: this.getChartColors(chartData.data?.length || 0),
                    borderColor: "#337ab7",
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: chartData.type === "pie" || chartData.type === "doughnut" },
                },
                ...chartData.options,
            },
        });
    }

    _updatePills(metricName, vizType) {
        this.container.querySelectorAll(`.viz-pill[data-metric="${metricName}"]`).forEach((p) => {
            p.classList.toggle("active", p.dataset.type === vizType);
        });
    }

    // ── HTML fragments ─────────────────────────────────────────

    _skeletonHTML() {
        return (
            '<div class="metric-skeleton">' +
            '  <div class="placeholder col-5 mb-2" style="height:.7rem"></div>' +
            '  <div class="placeholder col-12" style="height:var(--metric-chart-height)"></div>' +
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

    // ── Utilities ──────────────────────────────────────────────

    getChartColors(count) {
        const colors = [
            "#337ab7","#5cb85c","#f0ad4e","#d9534f","#5bc0de",
            "#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22",
            "#17becf","#ff7f0e","#2ca02c","#d62728","#9467bd",
        ];
        return colors.slice(0, count);
    }

    formatNumber(num) {
        if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
        if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
        return String(num);
    }
}
