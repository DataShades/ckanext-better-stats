import pytest

from ckanext.better_stats.model import MetricConfig, UserFavorite


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestMetricConfig:
    def test_upsert_creates_new(self) -> None:
        """Test that upsert correctly inserts a new configuration into the DB."""
        cfg = MetricConfig.upsert("test_metric", enabled=False, col_span=4, row_span=2)

        assert cfg.metric_name == "test_metric"
        assert cfg.enabled is False
        assert cfg.col_span == 4
        assert cfg.row_span == 2

        fetched = MetricConfig.for_metric("test_metric")
        assert fetched is not None
        assert fetched.id == cfg.id
        assert fetched.enabled is False

    def test_upsert_updates_existing(self) -> None:
        """Test that upsert correctly updates an existing configuration."""
        cfg = MetricConfig.upsert("test_metric", enabled=True, col_span=2)
        cfg_id = cfg.id

        cfg2 = MetricConfig.upsert("test_metric", col_span=6, row_span=3)
        assert cfg2.id == cfg_id
        assert cfg2.enabled is True
        assert cfg2.col_span == 6
        assert cfg2.row_span == 3

    def test_clear_all(self) -> None:
        """Test clearing all configurations."""
        MetricConfig.upsert("test_metric_1", enabled=True)
        MetricConfig.upsert("test_metric_2", enabled=False)

        assert MetricConfig.for_metric("test_metric_1") is not None
        assert MetricConfig.for_metric("test_metric_2") is not None

        MetricConfig.clear_all()

        assert MetricConfig.for_metric("test_metric_1") is None
        assert MetricConfig.for_metric("test_metric_2") is None


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestUserFavorite:
    def test_add_and_get(self) -> None:
        """Test adding and retrieving user favorites."""
        fav = UserFavorite.add("user_1", "test_metric_a")

        assert fav.user_id == "user_1"
        assert fav.metric_name == "test_metric_a"

        fetched = UserFavorite.get("user_1", "test_metric_a")
        assert fetched is not None
        assert fetched.id == fav.id

        # Missing favorite returns None
        assert UserFavorite.get("user_1", "test_metric_b") is None

    def test_metric_names_for_user(self) -> None:
        """Test retrieving all metric names favorited by a user."""
        UserFavorite.add("user_1", "test_metric_a")
        UserFavorite.add("user_1", "test_metric_b")
        UserFavorite.add("user_2", "test_metric_c")

        user_1_favs = UserFavorite.metric_names_for_user("user_1")
        assert user_1_favs == {"test_metric_a", "test_metric_b"}

        user_2_favs = UserFavorite.metric_names_for_user("user_2")
        assert user_2_favs == {"test_metric_c"}

    def test_remove(self) -> None:
        """Test removing a favorite."""
        fav = UserFavorite.add("user_1", "test_metric_a")
        assert UserFavorite.get("user_1", "test_metric_a") is not None

        fav.remove()
        assert UserFavorite.get("user_1", "test_metric_a") is None
