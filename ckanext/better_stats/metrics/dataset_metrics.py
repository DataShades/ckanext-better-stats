from sqlalchemy import func

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.better_stats.metrics.base import MetricBase


class DatasetCountMetric(MetricBase):
    """Simple dataset count metric"""

    def __init__(self):
        super().__init__(
            name="dataset_count",
            title="Total Datasets",
            description="Total number of datasets in the system",
            order=1,
        )

    def get_data(self):
        query = model.Session.query(model.Package).filter(
            model.Package.state == "active", model.Package.type == "dataset"
        )
        return query.count()

    def get_chart_data(self):
        count = self.get_data()

        return {
            "type": "doughnut",
            "data": [count, 0],  # [value, remaining] for gauge
            "labels": ["Datasets", ""],
            "max": count * 1.2,  # Set max to 120% of current for gauge
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
        return {
            "headers": ["Metric", "Value"],
            "rows": [["Total Datasets", self.get_data()]],
        }


class DatasetsByOrganizationMetric(MetricBase):
    """Dataset distribution by organization"""

    def __init__(self):
        super().__init__(
            name="datasets_by_org",
            title="Datasets by Organization",
            description="Distribution of datasets across organizations",
            order=2,
        )

    def get_data(self):
        query = (
            model.Session.query(
                model.Group.title, func.count(model.Package.id).label("count")
            )
            .join(model.Member, model.Group.id == model.Member.group_id)
            .join(model.Package, model.Member.table_id == model.Package.id)
            .filter(
                model.Package.state == "active",
                model.Package.type == "dataset",
                model.Group.type == "organization",
                model.Member.table_name == "package",
            )
            .group_by(model.Group.title)
        )

        return [{"organization": row.title, "count": row.count} for row in query.all()]

    def get_chart_data(self):
        data = self.get_data()
        return {
            "type": "pie",
            "labels": [item["organization"] for item in data],
            "data": [item["count"] for item in data],
        }

    def get_table_data(self):
        data = self.get_data()
        return {
            "headers": ["Organization", "Dataset Count"],
            "rows": [[item["organization"], item["count"]] for item in data],
        }


class DatasetCreationHistoryMetric(MetricBase):
    """Dataset creation history over time"""

    def __init__(self):
        super().__init__(
            name="dataset_creation_history",
            title="Dataset Creation History",
            description="Number of datasets created over time",
            order=3,
        )

    def get_data(self):
        # Get monthly dataset creation counts
        query = (
            model.Session.query(
                func.date_trunc("day", model.Package.metadata_created).label("month"),
                func.count(model.Package.id).label("count"),
            )
            .filter(model.Package.state == "active", model.Package.type == "dataset")
            .group_by("month")
            .order_by("month")
        )

        return [
            {"month": row.month.strftime("%Y-%m-%d"), "count": row.count}
            for row in query.all()
        ]

    def get_chart_data(self):
        data = self.get_data()

        print(data)

        return {
            "type": "line",
            "labels": [item["month"] for item in data],
            "data": [item["count"] for item in data],
        }

    def get_table_data(self):
        data = self.get_data()
        return {
            "headers": [tk._("Month"), "Datasets Created"],
            "rows": [[item["month"], item["count"]] for item in data],
        }
