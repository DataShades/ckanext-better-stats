ckan.module("bstats-stats-settings", function ($) {
    return {
        options: {
            clearAllUrl: null,
            resetUrl: null,
            batchOrderUrl: null,
        },

        initialize() {
            $.proxyAll(this, /_/);

            this._csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
            this._timers = {};
            this._pending = 0;

            this._initSortable();
            this.el[0].reset();

            this.el.find("#btn-clear-all-caches").on("click", this._onClearAll);
            this.el.find("#btn-reset-all").on("click", this._onResetAll);
            this.el.on("change", ".metric-field", this._onFieldChange);
            this.el.on("click", ".btn-clear-cache", this._onClearMetricCache);
        },

        _initSortable() {
            this._sortables = [];
            this.el.find("[data-group-tbody]").each((_, tbody) => {
                this._sortables.push(
                    Sortable.create(tbody, {
                        handle: ".sortable-handle",
                        animation: 150,
                        onEnd: this._onReorder,
                    })
                );
            });
        },

        _onReorder(evt) {
            const rows = Array.from(evt.to.querySelectorAll(".metric-row"));
            const items = rows.map((row, idx) => ({
                metric_name: row.dataset.metric,
                order: (idx + 1) * 10,
            }));
            this._setStatus(this._("Saving\u2026"));
            this._lock();
            this._apiPost(this.options.batchOrderUrl, items)
                .then(() => this._setStatus(this._("Order saved") + " \u2713", true))
                .catch((err) => {
                    const msg = Array.isArray(err?.error) ? err.error.join(", ") : (err?.error || "");
                    this._setStatus(this._("Failed to save order") + (msg ? ": " + msg : ""), false);
                })
                .finally(() => this._unlock());
        },

        _onFieldChange(e) {
            const row = $(e.target).closest(".metric-row")[0];
            if (!row) return;
            const metric = row.dataset.metric;
            clearTimeout(this._timers[metric]);
            this._timers[metric] = setTimeout(() => this._saveRow(row), 600);
        },

        _saveRow(row) {
            const tbody = row.closest("[data-group-tbody]");
            const allRows = Array.from(tbody.querySelectorAll(".metric-row"));
            const idx = allRows.indexOf(row);
            const payload = { order: (idx + 1) * 10 };

            $(row).find(".metric-field").each(function () {
                const field = this.dataset.field;
                if (this.type === "checkbox") payload[field] = this.checked;
                else if (this.type === "number") payload[field] = parseInt(this.value, 10) || 0;
                else payload[field] = this.value;
            });

            this._setStatus(this._("Saving\u2026"));
            this._lock();
            this._apiPost($(row).data("update-url"), payload)
                .then(() => this._setStatus(this._("Saved") + " \u2713", true))
                .catch((err) => {
                    const msg = Array.isArray(err.error) ? err.error.join(", ") : err.error;
                    this._setStatus(this._("Save failed") + ": " + msg, false);
                })
                .finally(() => this._unlock());
        },

        _onClearMetricCache(e) {
            const $btn = $(e.currentTarget);
            const row = $btn.closest(".metric-row")[0];
            $btn.prop("disabled", true).html('<i class="fa fa-spinner fa-spin"></i>');
            this._apiPost($(row).data("cache-url"), {})
                .then(() => {
                    $btn.prop("disabled", false).html('<i class="fa fa-refresh"></i>');
                    this._setStatus(this._("Cache cleared") + " \u2713", true);
                })
                .catch(() => {
                    $btn.prop("disabled", false).html('<i class="fa fa-refresh"></i>');
                    this._setStatus(this._("Failed to clear cache"), false);
                });
        },

        _onClearAll() {
            const $btn = this.el.find("#btn-clear-all-caches").prop("disabled", true);
            this._apiPost(this.options.clearAllUrl, {})
                .then((data) => {
                    $btn.prop("disabled", false);
                    this._setStatus(
                        this._("All caches cleared") + " (" + data.cleared.length + " " + this._("metrics") + ") \u2713",
                        true
                    );
                })
                .catch(() => {
                    $btn.prop("disabled", false);
                    this._setStatus(this._("Some caches failed to clear"), false);
                });
        },

        _onResetAll() {
            if (!confirm(this._("Reset all metric settings to their defaults? This cannot be undone."))) return;
            const $btn = this.el.find("#btn-reset-all").prop("disabled", true);
            this._apiPost(this.options.resetUrl, {})
                .then(() => {
                    this._setStatus(this._("Resetting\u2026"));
                    setTimeout(() => location.reload(), 800);
                })
                .catch(() => {
                    $btn.prop("disabled", false);
                    this._setStatus(this._("Reset failed"), false);
                });
        },

        _lock() {
            if (++this._pending === 1) {
                this.el.find(".metric-field").prop("disabled", true);
                this.el.find(".sortable-handle").css("cursor", "not-allowed");
                this._sortables.forEach((s) => s.option("disabled", true));
            }
        },

        _unlock() {
            if (--this._pending === 0) {
                this.el.find(".metric-field").prop("disabled", false);
                this.el.find(".sortable-handle").css("cursor", "grab");
                this._sortables.forEach((s) => s.option("disabled", false));
            }
        },

        _apiPost(url, body) {
            return fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this._csrf,
                },
                body: JSON.stringify(body),
            }).then((resp) =>
                resp.json().then((data) => {
                    if (!resp.ok) return Promise.reject(data);
                    return data;
                })
            );
        },

        /* msg     — text to display
         * success — true: clear after 3 s; false: keep until next action; omit: keep */
        _setStatus(msg, success) {
            const $el = this.el.find("#autosave-status");
            clearTimeout(this._statusTimer);
            $el.text(msg);
            if (success === true) {
                this._statusTimer = setTimeout(() => $el.text(""), 3000);
            }
        },
    };
});
