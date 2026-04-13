ckan.module("bstats-favorite", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            this.manager = null;
            this.container = this.el[0] as HTMLElement;

            ckan.pubsub.subscribe("bstats:manager-ready", (manager: any) => {
                this.manager = manager;
            });

            // Favorite toggle
            this.container.addEventListener("click", (e) => {
                const btn = (e.target as Element).closest(".favorite-btn") as HTMLElement | null;
                if (btn) this._toggleFavorite(btn.dataset.metric!, btn);
            });
        },

        async _toggleFavorite(metricName: string, btn: HTMLElement) {
            const headers: Record<string, string> = { "Content-Type": "application/json" };

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
        },

        _setStarState(metricName: string, isFavorite: boolean) {
            const container = this.container as HTMLElement;

            container.querySelectorAll<HTMLElement>(`.favorite-btn[data-metric="${metricName}"]`).forEach((btn) => {
                const icon = btn.querySelector("i");
                if (icon) icon.className = isFavorite ? "fa-solid fa-star fav-active" : "fa-regular fa-star";
                btn.dataset.favorited = isFavorite ? "true" : "false";
                btn.title = isFavorite ? "Remove from favorites" : "Add to favorites";
            });
        },

        _addFavCard(cardHtml: string, metricName: string) {
            const grid = document.getElementById("bstats-grid-favorites");
            if (!grid) return;

            grid.querySelector(".bstats-fav-empty")?.remove();

            const tmp = this.manager._el("div", { innerHTML: cardHtml });
            const newCard = tmp.firstElementChild as HTMLElement | null;
            if (!newCard) return;
            grid.appendChild(newCard);

            newCard.querySelectorAll("[data-bs-toggle='tooltip']").forEach((el) => new bootstrap.Tooltip(el));

            const vizType = this.manager.currentVizTypes[metricName] || this.defaultViz;
            this.manager.loadMetric(metricName, vizType, false, newCard);
            this._updateFavCount(grid);
        },

        _removeFavCard(metricName: string) {
            const grid = document.getElementById("bstats-grid-favorites");
            if (!grid) return;

            const card = grid.querySelector<HTMLElement>(`.metric-container[data-metric="${metricName}"]`);
            if (!card) return;

            const contentId = card.dataset.contentId ?? `fav-${metricName}`;
            const chart = this.manager.charts[contentId];
            if (chart) {
                (Array.isArray(chart) ? chart : [chart]).forEach((c) => c.dispose());
                delete this.manager.charts[contentId];
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
        },

        _updateFavCount(grid: HTMLElement) {
            const count = grid.querySelectorAll(".metric-container").length;
            const badge = this.container.querySelector(
                `.bstats-group-toggle[data-group="favorites"] .bstats-group-count`
            );
            if (badge) badge.textContent = String(count);
        }
    };
});
