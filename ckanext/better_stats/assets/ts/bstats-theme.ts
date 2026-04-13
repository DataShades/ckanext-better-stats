ckan.module("bstats-theme", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);

            this.manager = null;
            this._initTheme();

            document.getElementById("bstats-theme-toggle")?.addEventListener("click", this._onToggle);

            ckan.pubsub.subscribe("bstats:manager-ready", (manager: any) => {
                this.manager = manager;
            });
        },

        _initTheme() {
            if (localStorage.getItem("bstats-theme") === "dark") {
                this.el[0].dataset.bstatsTheme = "dark";
                this._updateIcon(true);
            }
        },

        _onToggle() {
            const dark = this.el[0].dataset.bstatsTheme !== "dark";
            this.el[0].dataset.bstatsTheme = dark ? "dark" : "";
            localStorage.setItem("bstats-theme", dark ? "dark" : "");
            this._updateIcon(dark);
            this._updateChartsTheme();
        },

        _updateIcon(dark: boolean) {
            const icon = document.querySelector("#bstats-theme-toggle i") as HTMLElement | null;
            if (icon) icon.className = dark ? "fa fa-sun" : "fa fa-moon";
        },

        _updateChartsTheme() {
            const dark = this.manager._isDark();
            Object.values(this.manager.charts).forEach((entry) => {
                (Array.isArray(entry) ? entry : [entry]).forEach((chart) => {
                    chart.setTheme(dark ? "dark" : {});
                    chart.setOption(chart._chartOptions || {});
                });
            });
        },
    };
});
