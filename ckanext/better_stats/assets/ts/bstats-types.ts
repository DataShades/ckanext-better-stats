export const VIZ = {
    CHART: "chart",
    TABLE: "table",
    CARD: "card",
    PROGRESS: "progress",
} as const;

// Visualization ids are open-ended: the four built-ins plus any type an
// extension registers a renderer for. Hence a plain string rather than a union
// of the built-ins.
export type VizType = string;
