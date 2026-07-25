"""Backward-compatible helpers for AIHelper knowledge index v2 items."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any


INDEX_SCHEMA_VERSION = "aihelper-knowledge-index-v2"
_ID_NAMESPACE = uuid.UUID("24d6d4ce-76c8-4a3d-a681-58cc2f3fa8f4")
_METADATA_FIELDS = {
    "aliases",
    "artifact_type",
    "checked_at",
    "claim_ids",
    "created_at_basis",
    "legacy_indexed",
    "project_evidence",
    "review_due",
    "source_ids",
    "status",
    "title_integrity",
    "visibility",
    "volatility",
}


def normalize_path(path: str) -> str:
    """Return the data-root-relative slash path used by storage and the index."""
    normalized = str(path).replace("\\", "/")
    for marker in ("/data/", "data/"):
        index = normalized.find(marker)
        if index != -1:
            normalized = normalized[index + len(marker) :]
            break
    return normalized.lstrip("/")


def stable_item_id(path: str) -> str:
    """Create a deterministic ID that survives content edits at the same path."""
    value = uuid.uuid5(_ID_NAMESPACE, normalize_path(path).casefold()).hex[:16]
    return f"KDOC-{value.upper()}"


def sha256_content(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _unique_strings(values: list[str] | tuple[str, ...] | str | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    if isinstance(values, str):
        values = [values]
    for value in values or []:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def build_item(
    *,
    title: str,
    path: str,
    tags: list[str] | None,
    created_at: str,
    content: str | None,
    metadata: dict[str, Any] | None = None,
    existing: dict[str, Any] | None = None,
    updated_at: str | None = None,
    path_exists: bool = True,
) -> dict[str, Any]:
    """Build or upgrade one item while preserving unknown forward fields."""
    old = dict(existing or {})
    item = dict(old)
    normalized_path = normalize_path(path)
    was_legacy = bool(existing) and "id" not in old

    item["title"] = str(title).strip()
    item["path"] = normalized_path
    item["tags"] = _unique_strings(tags)
    item["created_at"] = old.get("created_at") or created_at
    item.setdefault("id", stable_item_id(normalized_path))
    item.setdefault("artifact_type", "knowledge")
    item.setdefault("status", "needs-review")
    item.setdefault("checked_at", None)
    item.setdefault("review_due", None)
    item.setdefault("source_ids", [])
    item.setdefault("claim_ids", [])
    item.setdefault("project_evidence", [])
    item.setdefault("aliases", [])
    item.setdefault("visibility", "internal")
    item.setdefault("volatility", "unknown")
    item.setdefault("legacy_indexed", was_legacy)
    item.setdefault("title_integrity", "observed-input")
    item.setdefault(
        "created_at_basis",
        "legacy-existing-index" if was_legacy else "writer-timestamp",
    )
    item["path_exists_in_data"] = bool(path_exists)
    item["preview_only"] = False

    if content is not None:
        item["content_hash"] = sha256_content(content)
    else:
        item.setdefault("content_hash", None)

    for field, value in (metadata or {}).items():
        if field not in _METADATA_FIELDS:
            raise ValueError(f"Unsupported knowledge metadata field: {field}")
        if field in {"aliases", "claim_ids", "project_evidence", "source_ids"}:
            item[field] = _unique_strings(value)
        else:
            item[field] = value

    if existing and updated_at:
        item["updated_at"] = updated_at
    return item


def upsert_item(
    db: dict[str, Any],
    *,
    title: str,
    path: str,
    tags: list[str] | None,
    created_at: str,
    content: str | None,
    metadata: dict[str, Any] | None = None,
    updated_at: str | None = None,
    path_exists: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Upsert by normalized path; duplicate titles at different paths remain distinct."""
    db.setdefault("items", [])
    db["schema_version"] = INDEX_SCHEMA_VERSION
    normalized_path = normalize_path(path)
    for index, existing in enumerate(db["items"]):
        if normalize_path(existing.get("path", "")) != normalized_path:
            continue
        item = build_item(
            title=title,
            path=normalized_path,
            tags=tags,
            created_at=created_at,
            content=content,
            metadata=metadata,
            existing=existing,
            updated_at=updated_at or created_at,
            path_exists=path_exists,
        )
        db["items"][index] = item
        return "updated", item

    item = build_item(
        title=title,
        path=normalized_path,
        tags=tags,
        created_at=created_at,
        content=content,
        metadata=metadata,
        path_exists=path_exists,
    )
    db["items"].append(item)
    return "added", item
