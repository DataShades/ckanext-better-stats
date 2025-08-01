import psutil

from ckanext.better_stats.metrics.base import MetricBase


class MemoryMetric(MetricBase):
    """System memory usage"""

    def __init__(self):
        super().__init__(
            name="memory",
            title="System Memory Usage",
            description="Memory usage of the system",
            order=1,
        )

    def get_data(self):
        mem = psutil.virtual_memory()
        return {
            "total": format_bytes(mem.total),
            "used": format_bytes(mem.used),
            "free": format_bytes(mem.available),
        }

    def get_chart_data(self):
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

    def get_table_data(self):
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
    """System CPU usage"""

    def __init__(self):
        super().__init__(
            name="cpu",
            title="CPU Usage",
            description="Current CPU usage percentage",
            order=2,
        )

    def get_data(self):
        return {
            "total": psutil.cpu_percent(interval=0.5),
            "per_core": psutil.cpu_percent(interval=None, percpu=True),
        }

    def get_chart_data(self):
        data = self.get_data()
        # Combine total and per-core for a grouped bar chart
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

    def get_table_data(self):
        data = self.get_data()
        rows = [["Total", f"{data['total']}%"]]

        for i, core in enumerate(data["per_core"]):
            rows.append([f"Core {i}", f"{core}%"])

        return {
            "headers": ["Metric", "Value"],
            "rows": rows,
        }


class DiskUsageMetric(MetricBase):
    """System disk usage (per partition)"""

    def __init__(self):
        super().__init__(
            name="disk_usage",
            title="Disk Usage",
            description="Disk usage of each partition",
            grid_size="full",
            order=3,
        )

    def get_data(self):
        partitions = psutil.disk_partitions()
        data = []
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                data.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": format_bytes(usage.total),
                        "used": format_bytes(usage.used),
                        "free": format_bytes(usage.free),
                        "percent": usage.percent,
                    }
                )
            except PermissionError:
                continue  # skip partitions we can't access
        return data

    def get_chart_data(self):
        partitions = psutil.disk_partitions()
        charts = []
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
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
            except PermissionError:
                continue
        return charts

    def get_table_data(self):
        data = self.get_data()
        headers = ["Device", "Mountpoint", "Type", "Total", "Used", "Free", "Usage %"]
        rows = [
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
        ]
        return {
            "headers": headers,
            "rows": rows,
        }


def format_bytes(num_bytes: float) -> str:
    """Convert bytes to a human-readable format (e.g., MB, GB)"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"
