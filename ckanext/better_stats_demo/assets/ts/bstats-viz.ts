// Shared contract + runtime for the demo viz renderers.
//
// This is the single source of truth for what a renderer is (the `VizContext`
// / `VizRenderer` types) and how it plugs into core (`registerRenderer`). It is
// the only module that touches the global `ckan` object — every renderer just
// imports `registerRenderer` from here, so nothing is redeclared or leaked to
// the global scope.

declare const ckan: any;

export interface VizContext {
    contentId: string;
    theme: "dark" | "default";
    manager: any;
}

export type VizRenderer = (container: HTMLElement, data: any, ctx: VizContext) => void;

// Register a renderer on the global `ckan.bstats` registry. Mirrors core's
// `registerRenderer`, set up idempotently so this works whether this bundle
// loads before or after the core Better Stats bundle.
export function registerRenderer(type: string, fn: VizRenderer): void {
    ckan.bstats = ckan.bstats || {};
    ckan.bstats.renderers = ckan.bstats.renderers || {};
    ckan.bstats.renderers[type] = fn;
}
