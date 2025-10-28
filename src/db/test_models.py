"""Simple test to verify new schema models."""

from src.db.models import User, Asset, ProcessingMetrics, CostumePopularity, AssetType


def test_models_importable():
    """Verify all new models can be imported."""
    assert User is not None
    assert Asset is not None
    assert ProcessingMetrics is not None
    assert CostumePopularity is not None
    assert AssetType is not None