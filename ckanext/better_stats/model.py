import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

import ckan.plugins.toolkit as tk
from ckan import model


def _current_datetime():
    return datetime.now(tz=timezone.utc)


class MetricConfig(tk.BaseModel):
    __tablename__ = "better_stats_metric_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    order = Column(Integer, default=100)
    col_span = Column(Integer, default=3)
    row_span = Column(Integer, default=1)
    access_level = Column(String(20))
    cache_timeout = Column(Integer, default=3600)
    extras = Column(MutableDict.as_mutable(JSONB), default={})
    created = Column(DateTime, default=_current_datetime)
    modified = Column(DateTime, default=_current_datetime, onupdate=_current_datetime)

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
