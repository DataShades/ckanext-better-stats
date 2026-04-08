const { resolve } = require("path");
const { src, watch, dest } = require("gulp");
const sass = require("gulp-sass")(require("sass"));
const cleanCSS = require("gulp-clean-css");
const header = require("gulp-header");

const themeDir = resolve("ckanext/better_stats/assets/theme");
const assetsDir = resolve("ckanext/better_stats/assets");

const banner = "/* builded automatically, do not touch, styles are in assets/theme/*.scss */\n";

function build() {
    return src(resolve(themeDir, "styles.scss"))
        .pipe(
            sass({ outputStyle: "compressed" }).on("error", sass.logError)
        )
        .pipe(cleanCSS({ level: 2 }))
        .pipe(header(banner))
        .pipe(dest(resolve(assetsDir, "css")));
}

function buildDev() {
    return src(resolve(themeDir, "styles.scss"))
        .pipe(
            sass({ outputStyle: "expanded" }).on("error", sass.logError)
        )
        .pipe(dest(resolve(assetsDir, "css")));
}

function watchSource() {
    watch(themeDir + "/**/*.scss", { ignoreInitial: false }, buildDev);
}

exports.build = build;
exports.watch = watchSource;
