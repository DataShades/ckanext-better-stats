from enum import Enum


class AccessLevel(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"


class VisualizationType(Enum):
    CHART = "chart"
    TABLE = "table"
    CARD = "card"


class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    IMAGE = "image"


class GridSize(Enum):
    FULL = "full"
    HALF = "half"
    THIRD = "third"
