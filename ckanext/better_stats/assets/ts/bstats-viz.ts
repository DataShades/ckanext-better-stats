// Pluggable client-side visualization renderer registry.
//
// Extensions register a renderer for a custom visualization type (matching a
// backend `Visualization` id) via:
//
//     ckan.bstats.registerRenderer("user_map", (container, data, ctx) => { ... });
//
// The registry lives on the global `ckan.bstats` object — not on a manager
// instance — so registration order relative to the dashboard manager does not
// matter: portals register at script-load time, the manager reads at render
// time.

declare const ckan: any;

// `data` is the full metric payload from the API
// ({ name, title, data, type, ... }); the visualization-specific payload is
// `data.data`. `ctx` carries render context the renderer may need.
export interface VizContext {
    contentId: string;
    theme: "dark" | "default";
    manager: any;
}

export type VizRenderer = (container: HTMLElement, data: any, ctx: VizContext) => void;

interface BstatsGlobal {
    renderers: Record<string, VizRenderer>;
    registerRenderer: (type: string, fn: VizRenderer) => void;
}

function ensureRegistry(): BstatsGlobal {
    ckan.bstats = ckan.bstats || {};
    if (!ckan.bstats.renderers) ckan.bstats.renderers = {};
    if (!ckan.bstats.registerRenderer) {
        ckan.bstats.registerRenderer = (type: string, fn: VizRenderer) => {
            ckan.bstats.renderers[type] = fn;
        };
    }
    return ckan.bstats as BstatsGlobal;
}

export function registerRenderer(type: string, fn: VizRenderer): void {
    ensureRegistry().registerRenderer(type, fn);
}

export function getRenderer(type: string): VizRenderer | undefined {
    return ensureRegistry().renderers[type];
}
