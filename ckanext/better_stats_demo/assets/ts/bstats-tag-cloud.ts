// DEMO renderer for the custom `tag_cloud` visualization type.
//
// A dependency-free word cloud: each tag is a <span> whose font size scales
// with its count, so the bigger the number, the bigger the word. Deliberately
// uses no external library (unlike the map demo's Leaflet) to show that a
// custom viz can be pure DOM.
//
// Reads `{ tags: [{ text, count }], palette }` from the metric payload and
// registers itself on the global `ckan.bstats` renderer registry that core
// exposes. Pulled into `bstats-demo.min.js` via the `bstats-demo.ts` entry.

import { registerRenderer } from "./bstats-viz";

interface Tag {
    text: string;
    count: number;
    url?: string;
}

interface TagCloudPayload {
    tags?: Tag[];
    palette?: string[];
}

const MIN_FONT_PX = 13;
const MAX_FONT_PX = 46;
const DEFAULT_PALETTE = ["#2563eb", "#16a34a", "#f97316", "#db2777", "#7c3aed", "#0891b2"];

registerRenderer("tag_cloud", (container, data, ctx) => {
    const payload: TagCloudPayload = data?.data ?? {};
    const tags = payload.tags ?? [];
    const palette = payload.palette?.length ? payload.palette : DEFAULT_PALETTE;

    const holder = document.createElement("div");
    holder.className = "bstats-tag-cloud";
    container.appendChild(holder);

    if (!tags.length) {
        holder.innerHTML = '<div class="text-muted">No tags to display.</div>';
        return;
    }

    const counts = tags.map((t) => t.count);
    const min = Math.min(...counts);
    const max = Math.max(...counts);
    const span = max - min || 1;

    // Mix big and small words instead of rendering them in count order, so the
    // cloud reads as a cloud rather than a sorted list.
    const shuffled = [...tags].sort((a, b) => hash(a.text) - hash(b.text));

    shuffled.forEach((tag) => {
        // sqrt scale so a few very large counts don't dwarf everything else.
        const ratio = Math.sqrt((tag.count - min) / span);
        const size = Math.round(MIN_FONT_PX + ratio * (MAX_FONT_PX - MIN_FONT_PX));
        const color = palette[hash(tag.text) % palette.length];

        // Render as a link when the metric supplied a URL (real CKAN tag
        // search), otherwise a plain span. Either way it carries the cloud
        // styling and size-by-count.
        const el = document.createElement(tag.url ? "a" : "span");
        el.className = "bstats-tag";
        el.textContent = tag.text;
        el.style.fontSize = `${size}px`;
        // Heavier weight and fuller opacity for the more frequent tags.
        el.style.fontWeight = String(400 + Math.round(ratio * 400));
        el.style.opacity = String(0.55 + ratio * 0.45);
        el.style.color = color;
        el.title = `${tag.text}: ${tag.count}`;
        if (tag.url) {
            (el as HTMLAnchorElement).href = tag.url;
        }
        holder.appendChild(el);
    });
});

// Small deterministic hash of a string → used to shuffle and to pick a colour,
// so the layout is stable across renders but big words don't all clump first.
function hash(text: string): number {
    let h = 0;
    for (let i = 0; i < text.length; i++) {
        h = (h * 31 + text.charCodeAt(i)) >>> 0;
    }
    return h;
}
