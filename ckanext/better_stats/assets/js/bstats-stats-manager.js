ckan.module("bstats-stats-manager", function ($) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            // Initialize when DOM is ready
            $(document).ready(() => {
                new BetterStatsManager();
            });
        },
    };
});


class BetterStatsManager {
    constructor() {
        this.charts = {};
        this.currentVizTypes = {};
        this.init();
    }

    init() {
        console.log('Initializing Better Stats Manager');

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

                console.log(`Switching visualization for metric: ${metric} to type: ${type}`);

                this.switchVisualization(metric, type, e.currentTarget);
            });
        });

        // Refresh buttons
        document.querySelectorAll('.refresh-metric').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.refreshMetric(e.currentTarget.dataset.metric);
            });
        });

        document.getElementById('refresh-all').addEventListener('click', () => {
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
    }

    async loadAllMetrics() {
        const containers = document.querySelectorAll('.metric-container');

        for (const container of containers) {
            const metricName = container.dataset.metric;
            await this.loadMetric(metricName, 'chart');
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

            this.renderMetric(container, data, vizType);
            this.currentVizTypes[metricName] = vizType;

            // Update active button
            this.updateActiveButton(metricName, vizType);

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
        const canvas = document.createElement('canvas');
        canvas.className = 'metric-chart';
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        const chartData = data.data;

        console.log('creating chart');

        let chartConfig = {
            type: chartData.type || 'bar',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    data: chartData.data || [],
                    backgroundColor: this.getChartColors(chartData.data?.length || 0),
                    borderColor: '#337ab7',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: chartData.type === 'pie'
                    }
                }
            }
        };

        // Destroy existing chart if exists
        if (this.charts[data.name]) {
            this.charts[data.name].destroy();
        }

        this.charts[data.name] = new Chart(ctx, chartConfig);
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
