ckan.module("bstats-stats-manager", function ($) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            // Initialize when DOM is ready
            $(document).ready(() => {
                new BetterStatsManager(this.el[0]);
            });
        },
    };
});


class BetterStatsManager {
    constructor(container) {
        this.container = container;
        this.charts = {};
        this.currentVizTypes = {};
        this.init();
    }

    init() {
        this._registerChartBackground();
        this.bindEvents();
        this.loadAllMetrics();
    }

    bindEvents() {
        // Visualization toggle
        document.querySelectorAll('.viz-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (e.currentTarget.classList.contains('active')) {
                    return; // Already active, do nothing
                }

                const metric = e.currentTarget.dataset.metric;
                const type = e.currentTarget.dataset.type;

                this.switchVisualization(metric, type, e.currentTarget);
            });
        });

        // Refresh buttons
        document.querySelectorAll('.refresh-metric').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.refreshMetric(e.currentTarget.dataset.metric);
            });
        });

        // Refresh all button (doesn't exist on embed)
        document.getElementById('refresh-all')?.addEventListener('click', () => {
            this.refreshAllMetrics();
        });

        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const metric = e.currentTarget.dataset.metric;
                const format = e.currentTarget.dataset.format;
                this.exportMetric(metric, format);
            });
        });

        // Export PNG buttons
        document.querySelectorAll('.export-image-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportImage(e.currentTarget.dataset.metric);
            });
        });

        // Embed buttons — update modal content before it opens
        document.querySelectorAll('.bstats-embed-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const metric = e.currentTarget.dataset.metric;
                this.openEmbedModal(metric);
            });
        });

        // Copy-to-clipboard inside embed modals
        document.querySelectorAll('.bstats-copy-embed').forEach(btn => {
            btn.addEventListener('click', this.copyEmbedCode);
        });
    }

    async loadAllMetrics() {
        const containers = this.container.querySelectorAll('.metric-container');

        for (const container of containers) {
            const metricName = container.dataset.metric;
            const defaultViz = container.dataset.defaultViz || 'chart';
            await this.loadMetric(metricName, defaultViz);
        }
    }

    async loadMetric(metricName, vizType = 'chart', refresh = false) {
        const container = document.getElementById(`metric-${metricName}`);

        if (!container) return;

        try {
            container.innerHTML = '<div class="loading-indicator"><i class="fa fa-spinner fa-spin"></i> Loading...</div>';

            const url = `/better_stats/metric/${metricName}?type=${vizType}${refresh ? '&refresh=true' : ''}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Use the type the server actually served (may differ from requested
            // if the metric fell back to its default visualization).
            const servedType = data.type || vizType;

            this.renderMetric(container, data, servedType);
            this.currentVizTypes[metricName] = servedType;
            this.updateActiveButton(metricName, servedType);

        } catch (error) {
            container.innerHTML = `<div class="alert alert-danger">Error loading metric: ${error.message}</div>`;
        }
    }

    renderMetric(container, data, vizType) {
        container.innerHTML = '';

        switch (vizType) {
            case 'chart':
                this.renderChart(container, data);
                break;
            case 'table':
                this.renderTable(container, data);
                break;
            case 'card':
                this.renderCard(container, data);
                break;
        }
    }

    renderChart(container, data) {
        const chartData = data.data;

        // Destroy any previously created charts for this metric.
        const existing = this.charts[data.name];
        if (existing) {
            if (Array.isArray(existing)) {
                existing.forEach(c => c.destroy());
            } else {
                existing.destroy();
            }
            delete this.charts[data.name];
        }

        if (chartData.type === 'multi') {
            const wrapper = document.createElement('div');
            wrapper.className = 'metric-chart-multi';
            container.appendChild(wrapper);

            this.charts[data.name] = chartData.charts.map((subChart, i) => {
                const item = document.createElement('div');
                item.className = 'metric-chart-item';
                wrapper.appendChild(item);
                return this._createSingleChart(item, subChart, `${data.name}-${i}`, subChart.title);
            });
        } else {
            this.charts[data.name] = this._createSingleChart(container, chartData, data.name);
        }
    }

    /**
     * Register a new chart background plugin that will draw a background
     * on the canvas before drawing the chart.
     *
     * We need it to have a white background on the chart when the chart
     * is being exported as an image. Otherwise, the background will be
     * transparent.
     */
    _registerChartBackground() {
        Chart.register({
            id: 'chartjs-chart-background',
            beforeDraw: (chart, args, opts) => {
                const ctx = chart.canvas.getContext('2d');
                ctx.save();
                ctx.globalCompositeOperation = 'destination-over';
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, chart.width, chart.height);
                ctx.restore();
            }
        })
    }

    _createSingleChart(container, chartData, key, title = null) {
        if (title) {
            const label = document.createElement('p');
            label.className = 'metric-chart-label';
            label.textContent = title;
            container.appendChild(label);
        }

        const canvas = document.createElement('canvas');
        canvas.className = 'metric-chart';
        container.appendChild(canvas);

        return new Chart(canvas.getContext('2d'), {
            type: chartData.type || 'bar',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    data: chartData.data || [],
                    backgroundColor: this.getChartColors(chartData.data?.length || 0),
                    borderColor: '#337ab7',
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        display: chartData.type === 'pie' || chartData.type === 'doughnut',
                    },
                },
                ...chartData.options,
            },
        });
    }

    renderTable(container, data) {
        const tableData = data.data;

        const table = document.createElement('table');
        table.className = 'metric-table';

        // Headers
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        tableData.headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');

        tableData.rows.forEach(row => {
            const tr = document.createElement('tr');

            row.forEach(cell => {
                const td = document.createElement('td');
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
            container.innerHTML = '<div class="alert alert-info">Card view not available for this metric</div>';
            return;
        }

        const cardDiv = document.createElement('div');
        cardDiv.className = 'metric-card-display';

        const valueDiv = document.createElement('div');
        valueDiv.className = 'metric-card-value';
        valueDiv.textContent = this.formatNumber(cardData.value);

        const labelDiv = document.createElement('div');
        labelDiv.className = 'metric-card-label';
        labelDiv.textContent = cardData.label;

        cardDiv.appendChild(valueDiv);
        cardDiv.appendChild(labelDiv);
        container.appendChild(cardDiv);
    }

    async switchVisualization(metricName, vizType, button) {
        // Update active button
        const container = button.closest('.metric-container');
        container.querySelectorAll('.viz-toggle').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');

        // Load metric with new visualization
        await this.loadMetric(metricName, vizType);
    }

    async refreshMetric(metricName) {
        const currentVizType = this.currentVizTypes[metricName] || 'chart';
        await this.loadMetric(metricName, currentVizType, true);
    }

    async refreshAllMetrics() {
        const containers = document.querySelectorAll('.metric-container');

        for (const container of containers) {
            const metricName = container.dataset.metric;
            await this.refreshMetric(metricName);
        }
    }

    exportMetric(metricName, format) {
        const url = `/better_stats/export/${metricName}?format=${format}`;
        window.open(url, '_blank');
    }

    async exportImage(metricName) {
        const filename = `metric-${metricName}-${new Date().toISOString()}.png`;
        const chart = this.charts[metricName];
        const content = document.getElementById(`metric-${metricName}`);

        if (!content) {
            return;
        }

        if (chart && content.querySelector(".metric-chart")) {
            const singleChart = Array.isArray(chart) ? chart[0] : chart;
            const dataUrl = singleChart.toBase64Image('image/png', 1.0);
            this._triggerDownload(dataUrl, filename);
            return;
        }

        try {
            const result = await snapdom(content, { scale: 2 });
            await result.download({ format: 'png', filename: filename, backgroundColor: "#ffffff"});
        } catch (err) {
            console.error('PNG export failed:', err);
        }
    }

    _triggerDownload(dataUrl, filename) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = filename;
        link.click();
    }

    openEmbedModal(metricName) {
        const vizType = this.currentVizTypes[metricName] || 'chart';
        const embedUrl = `${window.location.origin}/better_stats/embed/${metricName}?viz=${encodeURIComponent(vizType)}`;
        const code = `<iframe src="${embedUrl}" width="600" height="400" frameborder="0" style="border:1px solid #e2e8f0;border-radius:8px"></iframe>`;

        // Update the textarea and live preview iframe
        const textarea = document.getElementById(`embedCode-${metricName}`);
        if (textarea) textarea.value = code;

        const preview = document.getElementById(`embedPreview-${metricName}`);
        if (preview) preview.src = embedUrl;
    }

    copyEmbedCode(e) {
        const targetId = e.currentTarget.dataset.target;
        const textarea = document.getElementById(targetId);
        if (!textarea) return;
        textarea.select();
        navigator.clipboard.writeText(textarea.value).then(() => {
            const icon = e.currentTarget.querySelector('i');
            if (icon) {
                icon.className = 'fa fa-check text-success';
                setTimeout(() => { icon.className = 'fa fa-clipboard'; }, 2000);
            }
        }).catch(() => {
            // Fallback for older browsers
            document.execCommand('copy');
        });
    }

    updateActiveButton(metricName, vizType) {
        const container = document.querySelector(`[data-metric="${metricName}"]`);
        if (container) {
            container.querySelectorAll('.viz-toggle').forEach(btn => {
                btn.classList.remove('active');
            });

            const activeButton = container.querySelector(`[data-type="${vizType}"]`);
            if (activeButton) {
                activeButton.classList.add('active');
            }
        }
    }

    getChartColors(count) {
        const colors = [
            '#337ab7', '#5cb85c', '#f0ad4e', '#d9534f', '#5bc0de',
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22',
            '#17becf', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'
        ];

        return colors.slice(0, count);
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
}
