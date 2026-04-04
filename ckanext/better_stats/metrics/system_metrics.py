from __future__ import annotations

from typing import Any, ClassVar

import psutil

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const
from ckanext.better_stats.metrics.base import MetricBase


class MemoryMetric(MetricBase):
    """System RAM usage (total, used, and free)."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = (
        const.VisualizationType.CHART
    )
    icon: ClassVar[str] = "bi-memory"
    color: ClassVar[str] = "#198754"

    def __init__(self) -> None:
        super().__init__(
            name="memory",
            title="System Memory Usage",
            description="Memory usage of the system",
            order=1,
        )

    @classmethod
    def get_access_level(cls) -> str:
        """Return the required access level value for this metric."""
        return const.AccessLevel.ADMIN.value

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
            "type": "doughnut",
            "data": [mem.used, mem.available],
            "labels": ["Used", "Free"],
            "max": mem.total,
            "rotation": -90,
            "aspectRatio": 2,
            "circumference": 180,
            "options": {
                "aspectRatio": 2,
                "circumference": 180,
                "rotation": -90,
            },
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


class CPUMetric(MetricBase):
    """Current CPU usage as a percentage (total and per-core)."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = (
        const.VisualizationType.CHART
    )
    icon: ClassVar[str] = "bi-cpu"
    color: ClassVar[str] = "#198754"

    def __init__(self) -> None:
        super().__init__(
            name="cpu",
            title="CPU Usage",
            description="Current CPU usage percentage",
            order=2,
            cache_timeout=15,
        )

    @classmethod
    def get_access_level(cls) -> str:
        """Return the required access level value for this metric."""
        return const.AccessLevel.ADMIN.value

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
            "type": "bar",
            "data": values,
            "labels": labels,
            "max": 100,
            "options": {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "max": 100,
                        "title": {"display": True, "text": "CPU Usage (%)"},
                    }
                },
                "aspectRatio": 2,
            },
        }

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        rows: list[list[str]] = [["Total", f"{data['total']}%"]]
        rows.extend(
            [f"Core {i}", f"{core}%"] for i, core in enumerate(data["per_core"])
        )
        return {
            "headers": ["Metric", "Value"],
            "rows": rows,
        }


class DiskUsageMetric(MetricBase):
    """Disk usage broken down by partition."""

    supported_visualizations: ClassVar[list[const.VisualizationType]] = [
        const.VisualizationType.CHART,
        const.VisualizationType.TABLE,
    ]
    default_visualization: ClassVar[const.VisualizationType] = (
        const.VisualizationType.TABLE
    )
    icon: ClassVar[str] = "bi-hdd"
    color: ClassVar[str] = "#198754"

    def __init__(self) -> None:
        super().__init__(
            name="disk_usage",
            title="Disk Usage",
            description="Disk usage of each partition",
            grid_size="full",
            order=3,
        )

    @classmethod
    def get_access_level(cls) -> str:
        """Return the required access level value for this metric."""
        return const.AccessLevel.ADMIN.value

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
        charts: list[dict[str, Any]] = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue
            charts.append(
                {
                    "type": "doughnut",
                    "data": [usage.used, usage.free],
                    "labels": ["Used", "Free"],
                    "max": usage.total,
                    "rotation": -90,
                    "aspectRatio": 2,
                    "circumference": 180,
                    "options": {
                        "aspectRatio": 2,
                        "circumference": 180,
                        "rotation": -90,
                    },
                    "title": f"{part.device} ({part.mountpoint})",
                }
            )
        return {"type": "multi", "charts": charts}

    def get_table_data(self) -> dict[str, Any]:
        data = self.get_data()
        return {
            "headers": [
                "Device", "Mountpoint", "Type",
                "Total", "Used", "Free", "Usage %",
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
