ckan.module("bstats-expand", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            this.manager = null;
            this._fullscreenChart = null;
            this._pendingFullscreen = null;
            this._pendingFullscreenContentId = null;

            ckan.pubsub.subscribe("bstats:manager-ready", (manager: any) => {
                this.manager = manager;
            });

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
                if (contentEl) {
                    contentEl.innerHTML = this.manager
                        ? this.manager._skeletonHTML()
                        : '<div class="metric-skeleton"><div class="placeholder col-12"></div></div>';
                }
            });

            fsModal?.addEventListener("shown.bs.modal", () => this._openFullscreen());
            fsModal?.addEventListener("hidden.bs.modal", () => this._closeFullscreen());
        },

        async _openFullscreen() {
            const metricName = this._pendingFullscreen;
            if (!metricName || !this.manager) return;

            const titleEl = document.getElementById("bstats-fullscreen-title");
            const contentEl = document.getElementById("bstats-fullscreen-content");
            if (!contentEl) return;

            const contentId = this._pendingFullscreenContentId ?? metricName;
            const vizType = this.manager.currentVizTypes[contentId] || this.manager.defaultViz;

            try {
                const resp = await fetch(ckan.url(`/better_stats/metric/${metricName}?type=${vizType}`));
                const data = await resp.json();
                if (data.error) throw new Error(data.error);

                if (titleEl) titleEl.textContent = data.title;
                contentEl.innerHTML = "";

                if (vizType === "chart") {
                    this._fullscreenChart = this.manager._createChart(contentEl, data.data);
                } else {
                    this.manager.renderMetric(contentEl, data, vizType);
                }
            } catch (err) {
                contentEl.innerHTML = this.manager._errorHTML(metricName, (err as Error).message);
            }
        },

        _closeFullscreen() {
            if (this._fullscreenChart) {
                this._fullscreenChart.dispose();
                this._fullscreenChart = null;
            }
            const contentEl = document.getElementById("bstats-fullscreen-content");
            if (contentEl) contentEl.innerHTML = "";
            this._pendingFullscreen = null;
            this._pendingFullscreenContentId = null;
        },
    };
});
