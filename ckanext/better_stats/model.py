import uuid
from datetime import datetime, timezone
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
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
        sa.Column("created", sa.DateTime(timezone=True), default=_current_datetime),
        sa.Column(
            "modified",
            sa.DateTime(timezone=True),
            default=_current_datetime,
            onupdate=_current_datetime,
        ),
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
    def upsert(cls, metric_name: str, **kwargs: str | int | bool) -> "MetricConfig":
        # Retry once: a concurrent upsert may insert the row between our
        # SELECT and INSERT, raising IntegrityError on the unique constraint.
        # On the second pass the row is visible and we fall into UPDATE.
        for attempt in range(2):
            obj = cls.for_metric(metric_name)

            if not obj:
                obj = cls(metric_name=metric_name)
                model.Session.add(obj)

            for k, v in kwargs.items():
                setattr(obj, k, v)

            try:
                model.Session.commit()
            except IntegrityError:
                model.Session.rollback()
                if attempt == 0:
                    continue
                raise
            return obj

        raise AssertionError("unreachable")

    @classmethod
    def clear_all(cls) -> None:
        model.Session.query(cls).delete()
        model.Session.commit()


class UserFavorite(tk.BaseModel):
    __table__ = sa.Table(
        "better_stats_user_favorite",
        tk.BaseModel.metadata,
        sa.Column("id", sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("user_id", sa.String, nullable=False),
        sa.Column("metric_name", sa.String, nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), default=_current_datetime),
        sa.UniqueConstraint("user_id", "metric_name", name="uq_bstats_user_favorite"),
    )

    id: Mapped[str]
    user_id: Mapped[str]
    metric_name: Mapped[str]
    created: Mapped[datetime]

    @classmethod
    def metric_names_for_user(cls, user_id: str) -> "set[str]":
        rows = model.Session.query(cls.metric_name).filter_by(user_id=user_id).all()
        return {r.metric_name for r in rows}

    @classmethod
    def get(cls, user_id: str, metric_name: str) -> "UserFavorite | None":
        return model.Session.query(cls).filter_by(user_id=user_id, metric_name=metric_name).first()

    @classmethod
    def add(cls, user_id: str, metric_name: str) -> "UserFavorite":
        fav = cls(user_id=user_id, metric_name=metric_name)
        model.Session.add(fav)
        try:
            model.Session.commit()
        except IntegrityError:
            # Concurrent toggle inserted the same (user_id, metric_name) row;
            # treat add() as idempotent and return what's already there.
            model.Session.rollback()
            existing = cls.get(user_id, metric_name)
            if existing is None:
                raise
            return existing
        return fav

    def remove(self) -> None:
        model.Session.delete(self)
        model.Session.commit()
