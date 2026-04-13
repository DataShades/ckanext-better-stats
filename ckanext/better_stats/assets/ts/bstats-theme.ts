ckan.module("bstats-theme", function ($: any) {
    return {
        initialize() {
            $.proxyAll(this, /_/);
            this._initTheme();
            document.getElementById("bstats-theme-toggle")?.addEventListener("click", this._onToggle);
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
            this.sandbox.publish("bstats:theme-changed", dark);
        },

        _updateIcon(dark: boolean) {
            const icon = document.querySelector("#bstats-theme-toggle i") as HTMLElement | null;
            if (icon) icon.className = dark ? "fa fa-sun" : "fa fa-moon";
        },
    };
});
