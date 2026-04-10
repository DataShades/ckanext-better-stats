from enum import Enum


class AccessLevel(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"


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
