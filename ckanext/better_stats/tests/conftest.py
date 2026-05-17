from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from factory.declarations import LazyFunction
from pytest_factoryboy import register

from ckan.tests import factories

from ckanext.better_stats import const
from ckanext.better_stats.metrics import MetricBase, MetricRegistry

fake = factories.fake


@pytest.fixture
def clean_db(reset_db: Any, migrate_db_for: Any, with_plugins: Any):
    """Apply plugin migrations whenever CKAN DB is cleaned.

    Depends on ``with_plugins`` so the plugin is loaded before
    ``migrate_db_for`` runs — otherwise CKAN cannot resolve the
    plugin's alembic config.
    """
    reset_db()

    migrate_db_for("better_stats")


@register(_name="organization")
class OrganizationFactory(factories.Organization):
    pass


class ResourceFactory(factories.Resource):
    pass


@register(_name="dataset")
class DatasetFactory(factories.Dataset):
    owner_org = LazyFunction(lambda: OrganizationFactory()["id"])


@register(_name="user")
class UserFactory(factories.UserWithToken):
    pass


@register(_name="sysadmin")
class SysadminFactory(factories.SysadminWithToken):
    pass


@pytest.fixture
def metric_factory() -> Callable[[], MetricBase]:
    """Factory for creating metric objects for testing purposes."""

    def _factory(class_attrs: dict[str, Any] | None = None, **kwargs: Any) -> MetricBase:
        """Factory for creating metric objects for testing purposes."""
        name = kwargs.get("name", fake.word())
        access_level = kwargs.get("access_level", const.AccessLevel.PUBLIC.value)

        class _Metric(MetricBase):
            def __init__(self, **kwargs: Any) -> None:
                kwargs.setdefault("name", name)
                kwargs.setdefault("access_level", access_level)
                super().__init__(**kwargs)

            def get_data(self) -> int:
                return 1

            def get_card_data(self) -> dict[str, Any]:
                return {"value": 1, "label": self.title}

        if class_attrs is not None:
            for k, v in class_attrs.items():
                setattr(_Metric, k, v)

        metric = _Metric(**kwargs)

        MetricRegistry.register(metric.name, _Metric)

        return metric

    return _factory


@pytest.fixture
def fresh_registry() -> Any:
    MetricRegistry.reset()
    yield
    MetricRegistry.reset()
