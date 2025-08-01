from abc import ABC, abstractmethod

import ckan.plugins.toolkit as tk

from ckanext.better_stats import const


class MetricBase(ABC):
    """Base class for all metrics"""

    def __init__(
        self,
        name: str,
        title="",
        description: str = "",
        grid_size: str = "half",
        order: int = 100,
    ):
        self.name = name
        self.title = title
        self.description = description
        self.grid_size = grid_size
        self.order = order
        self.cache_key = f"better_stats:metric:{name}"
        self.cache_timeout = 3600

    @abstractmethod
    def get_data(self) -> dict | list | int | float:
        """Get raw data for the metric"""
        pass

    @abstractmethod
    def get_chart_data(self):
        """Transform raw data for chart visualization"""
        pass

    @abstractmethod
    def get_table_data(self):
        """Transform raw data for table visualization"""
        pass

    def get_card_data(self):
        """Transform raw data for card visualization (simple number display)"""
        data = self.get_data()

        if isinstance(data, (int, float)):
            return {"value": data, "label": self.title}

        return None

    def get_cached_data(self) -> dict | list | int | float:
        """Get cached data or fetch new data"""
        # Implementation would use CKAN's cache system
        return self.get_data()

    def refresh_cache(self) -> None:
        """Refresh cached data"""
        pass

    @classmethod
    def can_export(cls):
        """Check if metric data can be exported"""
        return True

    def get_export_data(self):
        """Get data in export format"""
        return self.get_table_data()

    @classmethod
    def get_access_level(cls):
        """Get required access level for this metric"""
        return const.AccessLevel.PUBLIC.value


register_metrics_signal = tk.signals.ckanext.signal(
    "better_stats:register_metrics",
    "Register metrics for the better_stats extension",
)


class MetricRegistry:
    """Registry for all available metrics"""

    METRICS: dict[str, type[MetricBase]] = {}

    @classmethod
    def register(cls, name: str, metric_class: type[MetricBase]) -> None:
        """Register a metric class"""
        cls.METRICS[name] = metric_class

    @classmethod
    def get_metric(cls, name) -> MetricBase | None:
        """Get specific metric by name"""
        if not cls.METRICS:
            register_metrics_signal.send()

        metric = cls.METRICS.get(name)

        return metric() if metric else None

    @classmethod
    def get_all_metrics(cls):
        """Get all registered metrics"""
        # TODO: order?
        return cls.METRICS.values()

    @classmethod
    def get_enabled_metrics(cls):
        """Get only enabled metrics"""
        if not cls.METRICS:
            register_metrics_signal.send()

        return cls.get_all_metrics()
        return [
            metric
            for metric in cls.get_all_metrics()
            if tk.asbool(
                tk.config.get(f"ckanext.better_stats.{metric.name}.enabled", True)
            )
        ]
