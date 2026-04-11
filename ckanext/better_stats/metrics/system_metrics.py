from __future__ import annotations

from typing import Any, ClassVar

import psutil

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase


class MemoryMetric(MetricBase):
    """System RAM usage (total, used, and free)."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.PROGRESS,
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.PROGRESS
    icon: ClassVar[str] = "fa-solid fa-memory"
    group: ClassVar[const.MetricGroup] = const.OVERVIEW_GROUP

    def __init__(self) -> None:
        super().__init__(
            name="memory",
            title="System Memory Usage",
            description="Memory usage of the system",
            order=160,
            col_span=2,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> dict[str, Any]:
        mem = psutil.virtual_memory()
        return {
            "total": tk.h.bs_format_bytes(mem.total),
            "used": tk.h.bs_format_bytes(mem.used),
            "free": tk.h.bs_format_bytes(mem.available),
        }

    def get_chart_data(self) -> dict[str, Any]:
        mem = psutil.virtual_memory()
        return {
            "tooltip": {"trigger": "item"},
            "series": [
                {
                    "type": "pie",
                    "radius": ["50%", "90%"],
                    "center": ["50%", "75%"],
                    "startAngle": 180,
                    "endAngle": 360,
                    "data": [
                        {"name": "Used", "value": mem.used},
                        {"name": "Free", "value": mem.available},
                    ],
                }
            ],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": ["Metric", "Value"],
            "rows": [
                ["Total", data["total"]],
                ["Used", data["used"]],
                ["Free", data["free"]],
            ],
        }

    def get_progress_data(self) -> dict[str, Any]:
        mem = psutil.virtual_memory()
        used_gb = round(mem.used / (1024**3), 1)
        total_gb = round(mem.total / (1024**3), 1)
        return {
            "items": [
                {"label": "RAM", "value": used_gb, "max": total_gb, "unit": "GB"},
            ]
        }


class CPUMetric(MetricBase):
    """Current CPU usage as a percentage (total and per-core)."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.PROGRESS,
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.PROGRESS
    icon: ClassVar[str] = "fa-solid fa-microchip"
    group: ClassVar[const.MetricGroup] = const.OVERVIEW_GROUP

    def __init__(self) -> None:
        super().__init__(
            name="cpu",
            title="CPU Usage",
            description="Current CPU usage percentage",
            order=170,
            col_span=2,
            cache_timeout=15,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> dict[str, Any]:
        return {
            "total": psutil.cpu_percent(interval=0.5),
            "per_core": psutil.cpu_percent(interval=None, percpu=True),
        }

    def get_chart_data(self) -> dict[str, Any]:
        data = self.get_data()
        labels = ["Total"] + [f"Core {i}" for i in range(len(data["per_core"]))]
        values = [data["total"]] + data["per_core"]
        return {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": labels},
            "yAxis": {"type": "value", "name": "CPU Usage (%)"},
            "series": [{"type": "bar", "data": values, "colorBy": "data"}],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        rows: list[list[str]] = [["Total", f"{data['total']}%"]]
        rows.extend([f"Core {i}", f"{core}%"] for i, core in enumerate(data["per_core"]))
        return {
            "headers": ["Metric", "Value"],
            "rows": rows,
        }

    def get_progress_data(self) -> dict[str, Any]:
        data = self.get_data()
        items = [{"label": "Total", "value": data["total"], "max": 100, "unit": "%"}]
        items.extend(
            {"label": f"Core {i}", "value": core, "max": 100, "unit": "%"} for i, core in enumerate(data["per_core"])
        )
        return {"items": items}


class DiskUsageMetric(MetricBase):
    """Disk usage broken down by partition."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.PROGRESS,
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = const.VisualizationType.PROGRESS
    icon: ClassVar[str] = "fa-solid fa-hard-drive"
    group: ClassVar[const.MetricGroup] = const.OVERVIEW_GROUP

    def __init__(self) -> None:
        super().__init__(
            name="disk_usage",
            title="Disk Usage",
            description="Disk usage of each partition",
            order=180,
            col_span=4,
            access_level=const.AccessLevel.ADMIN.value,
        )

    def get_data(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue
            result.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total": tk.h.bs_format_bytes(usage.total),
                    "used": tk.h.bs_format_bytes(usage.used),
                    "free": tk.h.bs_format_bytes(usage.free),
                    "percent": usage.percent,
                }
            )
        return result

    def get_chart_data(self) -> dict[str, Any]:
        partitions = []
        used_values = []
        free_values = []

        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue
            partitions.append(part.mountpoint)
            used_values.append(round(usage.used / (1024**3), 2))
            free_values.append(round(usage.free / (1024**3), 2))
        return {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {},
            "grid": {"left": 120, "right": 20, "top": 40, "bottom": 20},
            "xAxis": {"type": "value", "name": "GB", "nameLocation": "end"},
            "yAxis": {"type": "category", "data": partitions},
            "series": [
                {"name": "Used", "type": "bar", "stack": "total", "data": used_values},
                {"name": "Free", "type": "bar", "stack": "total", "data": free_values},
            ],
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [
                "Device",
                "Mountpoint",
                "Type",
                "Total",
                "Used",
                "Free",
                "Usage %",
            ],
            "rows": [
                [
                    d["device"],
                    d["mountpoint"],
                    d["fstype"],
                    d["total"],
                    d["used"],
                    d["free"],
                    f"{d['percent']}%",
                ]
                for d in data
            ],
        }

    def get_progress_data(self) -> dict[str, Any]:
        items = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue
            items.append(
                {
                    "label": part.mountpoint,
                    "value": round(usage.used / (1024**3), 1),
                    "max": round(usage.total / (1024**3), 1),
                    "unit": "GB",
                }
            )
        return {"items": items}
