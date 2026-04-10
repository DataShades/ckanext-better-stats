from enum import Enum


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
