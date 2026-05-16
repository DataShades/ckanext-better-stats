from typing import Any

import pytest

from ckan import logic
from ckan.plugins import toolkit as tk

from ckanext.better_stats.model import MetricConfig


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestUpdateMetricAction:
    def test_update_metric_success(self, sysadmin: dict[str, Any]):
        """Sysadmins can update metrics successfully."""
        result = tk.get_action("better_stats_update_metric")(
            {"user": sysadmin["name"]},
            {
                "metric_name": "dataset_count",
                "enabled": False,
                "col_span": 5,
            },
        )

        assert result["metric"] == "dataset_count"
        assert result["enabled"] is False
        assert result["col_span"] == 5

        cfg = MetricConfig.for_metric("dataset_count")
        assert cfg is not None
        assert cfg.enabled is False
        assert cfg.col_span == 5

    def test_update_metric_not_found(self, sysadmin: dict[str, Any]):
        """Action raises ObjectNotFound for unregistered metrics."""
        with pytest.raises(tk.ObjectNotFound):
            tk.get_action("better_stats_update_metric")(
                {"user": sysadmin["name"]},
                {
                    "metric_name": "non_existent_metric",
                    "enabled": True,
                },
            )

    def test_update_metric_no_fields(self, sysadmin: dict[str, Any]):
        """Action raises ValidationError if no update fields are provided."""
        with pytest.raises(tk.ValidationError) as exc:
            tk.get_action("better_stats_update_metric")(
                {"user": sysadmin["name"]}, {"metric_name": "dataset_count", "unsupported_field": "test"}
            )
        assert "No valid fields provided" in str(exc.value)

    def test_update_metric_auth(self, user: dict[str, Any]):
        """Normal users cannot update metrics."""
        with pytest.raises(logic.NotAuthorized):
            tk.get_action("better_stats_update_metric")(
                {"user": user["name"]}, {"metric_name": "dataset_count", "col_span": 2}
            )
