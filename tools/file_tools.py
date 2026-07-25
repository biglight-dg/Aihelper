from datetime import datetime

from tools import storage
from tools.knowledge_index import INDEX_SCHEMA_VERSION, upsert_item

DB_REL = "knowledge_db.json"
KNOWLEDGE_DIR_REL = "knowledge"


def load_db() -> dict:
    return storage.read_json(
        DB_REL, {"schema_version": INDEX_SCHEMA_VERSION, "items": []}
    )


def save_db(db: dict) -> None:
    storage.write_json(DB_REL, db)


def save_knowledge_file(
    title: str,
    content: str,
    tags: list[str] | None = None,
    metadata: dict | None = None,
) -> str:
    """정리된 지식을 knowledge/ 에 Markdown으로 저장하고 상대경로를 반환."""
    safe_title = (
        "".join(c if c.isalnum() or c in " _-" else "_" for c in title).strip()
        or "untitled"
    )
    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{safe_title[:40]}.md"
    relpath = f"{KNOWLEDGE_DIR_REL}/{filename}"

    storage.write_text(relpath, content)

    db = load_db()
    upsert_item(
        db,
        title=title,
        path=relpath,
        tags=tags,
        created_at=now.isoformat(),
        content=content,
        metadata=metadata,
        path_exists=True,
    )
    save_db(db)

    return relpath
