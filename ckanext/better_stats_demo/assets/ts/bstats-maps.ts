// DEMO renderer for the custom, data-driven `map` visualization type.
//
// Shows how a portal can plug an arbitrary third-party widget (here: a Leaflet
// map, with Leaflet shipped as a page asset via webassets.yml) into a Better
// Stats metric card, with no changes to the core renderer — it registers itself
// on the global `ckan.bstats` renderer registry that core exposes.
//
// A *single* `map` viz type backs every demo map metric. What the map looks
// like is decided entirely by the metric's data payload:
//
//   { points, tiles, style, color }
//
//   * `tiles`  — a named basemap preset ("osm" | "topo" | "satellite")
//   * `style`  — how points are drawn ("circles" | "pins" | "heat")
//   * `color`  — accent colour for "circles"/"pins"
//
// So three metrics (Users by Origin, Datasets by Region, Download Activity) all
// "fall under" one viz type yet render with different tiles and markers.
//
// This bundle is shipped by the `better_stats_demo` plugin; drop that plugin
// (and the matching demo metrics / `map` viz) to remove the demo.

import { registerRenderer, type VizContext } from "./bstats-viz";

// Leaflet (+ the leaflet.heat plugin) is loaded as a page asset via
// `webassets.yml` — js/vendor/leaflet.js and leaflet-heat.js are bundled ahead
// of this file — so the global `L` is always present by the time a map renders.
declare const L: any;

interface MapPoint {
    name: string;
    lat: number;
    lng: number;
    count: number;
}

interface MapPayload {
    points?: MapPoint[];
    tiles?: string;
    style?: "circles" | "pins" | "heat";
    color?: string;
}

interface TileLayerSpec {
    url: string;
    attribution: string;
    maxZoom?: number;
}

// Named basemap presets. Each can offer a `dark` override; where it doesn't,
// the light tiles read fine on the dark UI (terrain/satellite imagery), so we
// fall back to them. The metric only ships the preset *name*, keeping the
// backend free of tile URLs.
const TILE_PRESETS: Record<string, { light: TileLayerSpec; dark?: TileLayerSpec }> = {
    osm: {
        light: {
            url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 8,
        },
        dark: {
            url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
            maxZoom: 8,
        },
    },
    topo: {
        light: {
            url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            attribution: "&copy; OpenTopoMap (CC-BY-SA)",
            maxZoom: 7,
        },
    },
    satellite: {
        light: {
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution: "Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics",
            maxZoom: 8,
        },
    },
};

function resolveTiles(name: string | undefined, theme: VizContext["theme"]): TileLayerSpec {
    const preset = TILE_PRESETS[name ?? "osm"] ?? TILE_PRESETS.osm;
    return theme === "dark" ? preset.dark ?? preset.light : preset.light;
}

// A holder div with an explicit height — the card body has none, so Leaflet
// would otherwise collapse to 0px.
function makeHolder(container: HTMLElement): HTMLElement {
    const holder = document.createElement("div");
    holder.className = "bstats-map";
    holder.style.height = "100%";
    holder.style.width = "100%";
    holder.style.borderRadius = "8px";
    holder.style.overflow = "hidden";
    container.appendChild(holder);
    return holder;
}

// "circles": scaled circle markers (the original Users-by-Origin look).
function drawCircles(L: any, map: any, points: MapPoint[], color: string): void {
    const max = points.reduce((m, p) => Math.max(m, p.count), 0) || 1;
    points.forEach((p) => {
        // Size scales with the point's share of the busiest one, with a small
        // floor so low-count points stay visible as distinct pins.
        const radius = 5 + Math.round(Math.sqrt(p.count / max) * 12);
        L.circleMarker([p.lat, p.lng], {
            radius,
            color,
            fillColor: color,
            fillOpacity: p.count ? 0.6 : 0.25,
            weight: 1,
        })
            .bindTooltip(`${p.name}: ${p.count}`, { direction: "top" })
            .addTo(map);
    });
}

// "pins": square divIcon badges showing the value — distinct from circles.
function drawPins(L: any, map: any, points: MapPoint[], color: string): void {
    const max = points.reduce((m, p) => Math.max(m, p.count), 0) || 1;
    points.forEach((p) => {
        const size = 18 + Math.round(Math.sqrt(p.count / max) * 16);
        const icon = L.divIcon({
            className: "bstats-map-pin",
            html:
                `<div style="width:${size}px;height:${size}px;background:${color};` +
                "color:#fff;border:2px solid rgba(255,255,255,.85);border-radius:4px;" +
                "display:flex;align-items:center;justify-content:center;" +
                `font-size:11px;font-weight:600;box-shadow:0 1px 4px rgba(0,0,0,.4);">` +
                `${p.count}</div>`,
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2],
        });
        L.marker([p.lat, p.lng], { icon })
            .bindTooltip(`${p.name}: ${p.count}`, { direction: "top" })
            .addTo(map);
    });
}

// "heat": a heatmap layer (requires the leaflet.heat plugin).
function drawHeat(L: any, map: any, points: MapPoint[]): void {
    const max = points.reduce((m, p) => Math.max(m, p.count), 0) || 1;
    const heatPoints = points.map(
        (p) => [p.lat, p.lng, p.count / max] as [number, number, number],
    );
    L.heatLayer(heatPoints, {
        radius: 22,
        blur: 18,
        maxZoom: 6,
        minOpacity: 0.35,
    }).addTo(map);
}

registerRenderer("map", (container, data, ctx) => {
    const payload: MapPayload = data?.data ?? {};
    const points = payload.points ?? [];
    const style = payload.style ?? "circles";
    const color = payload.color ?? "#3b82f6";

    const holder = makeHolder(container);

    const tiles = resolveTiles(payload.tiles, ctx.theme);
    const map = L.map(holder, { attributionControl: true }).setView([20, 0], 1);
    L.tileLayer(tiles.url, {
        attribution: tiles.attribution,
        maxZoom: tiles.maxZoom ?? 8,
    }).addTo(map);

    if (style === "heat") {
        drawHeat(L, map, points);
    } else if (style === "pins") {
        drawPins(L, map, points, color);
    } else {
        drawCircles(L, map, points, color);
    }

    // Leaflet miscalculates size when initialised in a hidden/animating
    // container (e.g. the expand modal); nudge it once laid out.
    requestAnimationFrame(() => map.invalidateSize());
});
