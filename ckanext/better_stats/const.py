from dataclasses import dataclass
from enum import Enum

import ckan.plugins.toolkit as tk


class AccessLevel(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"


class MetricScope(Enum):
    GLOBAL = "global"
    USER = "user"


class VisualizationType(Enum):
    CHART = "chart"
    TABLE = "table"
    CARD = "card"
    PROGRESS = "progress"


class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    IMAGE = "image"


@dataclass
class MetricGroup:
    name: str
    label: str
    icon: str = ""
    description: str = ""


DATASETS_GROUP = MetricGroup(name="datasets", label=tk._("Datasets"), icon="fa-solid fa-file-alt")
ORGANIZATIONS_GROUP = MetricGroup(name="organizations", label=tk._("Organizations"), icon="fa-solid fa-building-user")
OVERVIEW_GROUP = MetricGroup(name="overview", label=tk._("Overview"), icon="fa-solid fa-bolt-lightning")
GENERAL_GROUP = MetricGroup(name="general", label=tk._("General"), icon="fa-solid fa-chart-bar")
FAVORITES_GROUP = MetricGroup(name="favorites", label=tk._("Favorites"), icon="fa fa-star")
