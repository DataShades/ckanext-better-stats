// esbuild entry for `bstats-demo.min.js`.
//
// Pulls in every demo renderer purely for its side effect: each module calls
// `registerRenderer(...)` at import time, registering itself on core's global
// `ckan.bstats` registry. Add a new demo viz by creating its renderer module
// and importing it here. Shared types/runtime live in `bstats-viz.ts`.

import "./bstats-maps";
import "./bstats-tag-cloud";
