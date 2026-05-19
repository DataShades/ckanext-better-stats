export const VIZ = {
    CHART: "chart",
    TABLE: "table",
    CARD: "card",
    PROGRESS: "progress",
} as const;

export type VizType = (typeof VIZ)[keyof typeof VIZ];
