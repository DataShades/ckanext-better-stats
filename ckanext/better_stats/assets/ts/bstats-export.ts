declare const ckan: any;
declare const snapdom: any;

ckan.module("bstats-export", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            // Export CSV / JSON
            this.el[0].addEventListener("click", (e) => {
                const btn = (e.target as Element).closest(".export-btn") as HTMLElement | null;
                if (btn) {
                    e.preventDefault();
                    ckan.pubsub.publish("bstats:export", btn.dataset.metric!, btn.dataset.format!);
                    this._onExport(btn.dataset.metric!, btn.dataset.format!);
                }
            });

            // Export PNG
            this.el[0].addEventListener("click", (e) => {
                const btn = (e.target as Element).closest(".export-image-btn") as HTMLElement | null;
                if (btn) {
                    e.preventDefault();
                    const card = btn.closest<HTMLElement>(".metric-container");
                    const contentId = card?.dataset.contentId ?? btn.dataset.metric!;
                    this._onExportImage(btn.dataset.metric!, contentId);
                }
            });
        },

        _onExport(metricName: string, format: string) {
            window.open(ckan.url(`/better_stats/export/${metricName}?format=${format}`), "_blank");
        },

        async _onExportImage(metricName: string, contentId: string) {
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
        },
    };
});
