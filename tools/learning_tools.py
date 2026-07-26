"""Structured Phase 4 learning assets used by the AIHelper learning lab."""

from tools import storage

LEARNING_ASSETS_REL = "learning_assets.json"


def load_learning_assets_db() -> dict:
    """Return the learning asset catalog, or an empty versioned catalog."""
    return storage.read_json(
        LEARNING_ASSETS_REL,
        {"schema_version": "aihelper-learning-assets-v1", "items": []},
    )


def get_learning_asset(asset_id: str) -> dict | None:
    """Find one learning asset by its stable id."""
    return next(
        (
            item
            for item in load_learning_assets_db().get("items", [])
            if item.get("id") == asset_id
        ),
        None,
    )
