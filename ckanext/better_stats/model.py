import uuid
from datetime import datetime, timezone
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped

import ckan.plugins.toolkit as tk
from ckan import model


def _current_datetime():
    return datetime.now(tz=timezone.utc)


class MetricConfig(tk.BaseModel):
    __table__ = sa.Table(
        "better_stats_metric_config",
        tk.BaseModel.metadata,
        sa.Column("id", sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("metric_name", sa.String, nullable=False, index=True),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column("order", sa.Integer, default=100),
        sa.Column("col_span", sa.Integer, default=3),
        sa.Column("row_span", sa.Integer, default=1),
        sa.Column("access_level", sa.String(20)),
        sa.Column("cache_timeout", sa.Integer, default=3600),
        sa.Column("extras", MutableDict.as_mutable(JSONB), default={}),
        sa.Column("created", sa.DateTime, default=_current_datetime),
        sa.Column("modified", sa.DateTime, default=_current_datetime, onupdate=_current_datetime),
    )

    id: Mapped[str]
    metric_name: Mapped[str]
    enabled: Mapped[bool]
    order: Mapped[int]
    col_span: Mapped[int]
    row_span: Mapped[int]
    access_level: Mapped[str]
    cache_timeout: Mapped[int]
    extras: Mapped[dict[str, Any]]
    created: Mapped[datetime]
    modified: Mapped[datetime]

    @classmethod
    def for_metric(cls, metric_name: str) -> "MetricConfig | None":
        return model.Session.query(cls).filter_by(metric_name=metric_name).first()

    @classmethod
    def upsert(cls, metric_name: str, **kwargs: dict[str, str | int | bool]) -> "MetricConfig":
        obj = cls.for_metric(metric_name)

        if not obj:
            obj = cls(metric_name=metric_name)
            model.Session.add(obj)

        for k, v in kwargs.items():
            setattr(obj, k, v)

        model.Session.commit()

        return obj

    @classmethod
    def clear_all(cls) -> None:
        model.Session.query(cls).delete()
        model.Session.commit()
