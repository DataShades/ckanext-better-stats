from __future__ import annotations

from unittest import mock

import pytest

from ckanext.better_stats.metrics.system_metrics import (
    CPUMetric,
    DiskUsageMetric,
    MemoryMetric,
)


@pytest.mark.usefixtures("with_plugins")
class TestSystemMetrics:
    def test_memory_get_data_uses_psutil(self) -> None:
        with mock.patch("ckanext.better_stats.metrics.system_metrics.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = mock.Mock(
                total=8 * 1024**3, used=4 * 1024**3, available=4 * 1024**3
            )
            data = MemoryMetric().get_data()

        assert data["total"] == "8.00 GB"
        assert data["used"] == "4.00 GB"
        assert data["free"] == "4.00 GB"

    def test_memory_chart_progress_table(self) -> None:
        with mock.patch("ckanext.better_stats.metrics.system_metrics.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = mock.Mock(
                total=8 * 1024**3, used=4 * 1024**3, available=4 * 1024**3
            )
            metric = MemoryMetric()

        assert metric.get_chart_data()["series"][0]["type"] == "pie"
        assert metric.get_progress_data()["items"][0]["unit"] == "GB"
        assert metric.get_table_data()["headers"]

    def test_cpu_metric(self) -> None:
        with mock.patch("ckanext.better_stats.metrics.system_metrics.psutil") as mock_psutil:
            mock_psutil.cpu_percent.side_effect = [10.0, [5.0, 15.0]] * 4
            metric = CPUMetric()

            data = metric.get_data()
            table = metric.get_table_data()
            progress = metric.get_progress_data()

        assert data["total"] == 10.0
        assert data["per_core"] == [5.0, 15.0]
        assert metric.get_chart_data()["series"][0]["type"] == "bar"
        assert len(table["rows"]) == 3
        assert len(progress["items"]) == 3

    def test_disk_usage_metric(self) -> None:
        fake_partition = mock.Mock(device="/dev/sda1", mountpoint="/", fstype="ext4")
        fake_usage = mock.Mock(total=100 * 1024**3, used=50 * 1024**3, free=50 * 1024**3, percent=50)

        with mock.patch("ckanext.better_stats.metrics.system_metrics.psutil") as mock_psutil:
            mock_psutil.disk_partitions.return_value = [fake_partition]
            mock_psutil.disk_usage.return_value = fake_usage
            metric = DiskUsageMetric()
            data = metric.get_data()
            assert len(data) == 1
            assert metric.get_chart_data()["series"][0]["type"] == "bar"
            assert metric.get_table_data()["headers"]
            assert len(metric.get_progress_data()["items"]) == 1

    def test_disk_usage_skips_permission_error(self) -> None:
        fake_partition = mock.Mock(device="/dev/sda1", mountpoint="/", fstype="ext4")
        with mock.patch("ckanext.better_stats.metrics.system_metrics.psutil") as mock_psutil:
            mock_psutil.disk_partitions.return_value = [fake_partition]
            mock_psutil.disk_usage.side_effect = PermissionError
            metric = DiskUsageMetric()
            assert metric.get_data() == []
            assert metric.get_chart_data()["series"][0]["data"] == []
            assert metric.get_progress_data()["items"] == []
