import uuid
from datetime import UTC, datetime

import ckan.plugins.toolkit as tk
from ckan import model
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict


def _current_datetime():
    return datetime.now(tz=UTC)


class MetricConfig(tk.BaseModel):
    __tablename__ = "better_stats_metric_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String(100), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    order = Column(Integer, default=100)
    grid_size = Column(String(10), default="half")  # "half" | "full" | "third"
    access_level = Column(String(20), default="public")
    cache_timeout = Column(Integer, default=3600)
    extras = Column(MutableDict.as_mutable(JSONB), default={})
    created = Column(DateTime, default=_current_datetime)
    modified = Column(DateTime, default=_current_datetime, onupdate=_current_datetime)

    @classmethod
    def for_metric(cls, metric_name: str) -> "MetricConfig | None":
        return model.Session.query(cls).filter_by(metric_name=metric_name).first()

    @classmethod
    def upsert(cls, metric_name: str, **kwargs) -> "MetricConfig":
        obj = cls.for_metric(metric_name)

        if not obj:
            obj = cls(metric_name=metric_name)
            model.Session.add(obj)

        for k, v in kwargs.items():
            setattr(obj, k, v)

        model.Session.commit()

        return obj
