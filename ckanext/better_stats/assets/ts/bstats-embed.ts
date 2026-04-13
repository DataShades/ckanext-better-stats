ckan.module("bstats-embed", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            const container = this.el[0] as HTMLElement;

            // Embed modal — stamp the current viz onto the trigger button so the
            // embed module can read it from relatedTarget in show.bs.modal.
            container.addEventListener("click", (e) => {
                const btn = (e.target as Element).closest(".bstats-embed-btn") as HTMLElement | null;
                if (btn) {
                    const card = btn.closest<HTMLElement>(".metric-container");
                    const contentId = card?.dataset.contentId ?? btn.dataset.metric!;
                    btn.dataset.embedViz = this.currentVizTypes[contentId] || this.defaultViz;
                }
            });

            container.addEventListener("click", (e) => {
                const btn = (e.target as Element).closest(".bstats-embed-btn") as HTMLElement | null;
                if (btn) this._onEmbedOpen(btn);
            });

            container.addEventListener("click", (e) => {
                const btn = (e.target as Element).closest(".bstats-copy-embed") as HTMLElement | null;
                if (btn) this._onCopyEmbed(btn);
            });
        },

        _onEmbedOpen(btn: HTMLElement) {
            const metricName = btn.dataset.metric!;
            const vizType = btn.dataset.embedViz || "chart";
            const embedUrl = ckan.url(`/better_stats/embed/${metricName}?viz=${encodeURIComponent(vizType)}`);
            const code = `<iframe src="${embedUrl}" width="600" height="400" frameborder="0" style="border:1px solid #e2e8f0;border-radius:8px"></iframe>`;

            const textarea = document.getElementById(`embedCode-${metricName}`) as HTMLTextAreaElement | null;
            if (textarea) textarea.value = code;

            const preview = document.getElementById(`embedPreview-${metricName}`) as HTMLIFrameElement | null;
            if (!preview) return;

            const wrapper = preview.closest(".bstats-embed-preview-wrap") as HTMLElement | null;

            preview.classList.remove("bstats-embed-preview--ready");
            if (wrapper) wrapper.classList.add("bstats-embed-preview--loading");

            preview.onload = () => {
                preview.classList.add("bstats-embed-preview--ready");
                if (wrapper) wrapper.classList.remove("bstats-embed-preview--loading");
                preview.onload = null;
            };

            preview.src = embedUrl;
        },

        _onCopyEmbed(btn: HTMLElement) {
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
        },
    };
});
