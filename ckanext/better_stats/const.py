from enum import Enum


class AccessLevel(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"


class VisualizationType(Enum):
    CHART = "chart"
    TABLE = "table"
    CARD = "card"
