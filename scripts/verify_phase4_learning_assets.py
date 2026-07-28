"""Verify generated Phase 4 delivery data and its Streamlit views."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.curriculum import validate_slides_data
from tools import storage
from tools.curriculum_tools import build_markdown_doc, build_session_doc

COURSE_ID = "cur_phase4_14_domain_foundations"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_data(data_root: Path) -> dict:
    manifest = _read_json(data_root / "phase4-learning-manifest.json")
    for rel, expected in manifest["files"].items():
        path = data_root / rel
        if not path.exists():
            raise AssertionError(f"manifest target missing: {rel}")
        observed = _sha256(path)
        if observed != expected["sha256"]:
            raise AssertionError(f"hash mismatch: {rel}: {observed}")

    course = _read_json(data_root / "curricula" / "phase4-14-domain-foundations.json")
    assets = _read_json(data_root / "learning_assets.json")["items"]
    tips = [
        item for item in _read_json(data_root / "ai_tips.json")["items"]
        if str(item.get("id", "")).startswith("TIP-P4-")
    ]
    slides = _read_json(data_root / "curricula" / "phase4-14-domain-foundations_slides.json")["slides"]

    if course.get("id") != COURSE_ID or len(course.get("sessions", [])) != 14:
        raise AssertionError("course id/session count mismatch")
    if len(assets) != 14 or len(tips) != 14:
        raise AssertionError("learning asset/tip count mismatch")
    errors = validate_slides_data(slides)
    if errors:
        raise AssertionError("slide validation failed: " + "; ".join(errors))

    for session in course["sessions"]:
        for field in ("knowledge_refs", "tip_refs", "checklist_refs"):
            refs = session.get(field, [])
            if len(refs) != 1 or not (data_root / refs[0]).exists():
                raise AssertionError(f"{session['id']}: broken {field}")
        if len(session.get("objectives", [])) != 3:
            raise AssertionError(f"{session['id']}: objective count mismatch")
        if len(session.get("activities", [])) != 3:
            raise AssertionError(f"{session['id']}: activity count mismatch")
        if len(session.get("assessment", {}).get("quiz", [])) != 3:
            raise AssertionError(f"{session['id']}: quiz count mismatch")

    original_root = storage.DATA_ROOT
    original_backend = storage._BACKEND
    try:
        storage.DATA_ROOT = data_root
        storage._BACKEND = None
        session_doc = build_session_doc(course, course["sessions"][5])
        full_doc = build_markdown_doc(course)
    finally:
        storage.DATA_ROOT = original_root
        storage._BACKEND = original_backend
    required = ("학습 흐름", "바로 쓰는 팁", "작업 예시", "실습 안내", "통과 기준", "확인 문제")
    for label in required:
        if label not in session_doc:
            raise AssertionError(f"session textbook missing section: {label}")
    if "artifact_type:" in session_doc or "artifact_type:" in full_doc:
        raise AssertionError("source frontmatter leaked into textbook")

    return {
        "sessions": len(course["sessions"]),
        "learning_assets": len(assets),
        "phase4_tips": len(tips),
        "slides": len(slides),
        "textbook_sections": list(required),
    }


def verify_app(data_root: Path) -> list[str]:
    from streamlit.testing.v1 import AppTest

    original_root = storage.DATA_ROOT
    original_backend = storage._BACKEND
    tested = []
    try:
        storage.DATA_ROOT = data_root
        storage._BACKEND = None
        for page in (
            "🎓 학습 홈",
            "📚 지식 베이스",
            "📋 커리큘럼",
            "🧪 실습·체크",
            "💡 AI 꿀팁",
        ):
            at = AppTest.from_file(str(REPO_ROOT / "app.py"))
            at.session_state["auth_ok"] = True
            at.session_state["role"] = "admin"
            at.session_state["nav_page"] = page
            at.run(timeout=45)
            if at.exception:
                raise AssertionError(f"AppTest failed for {page}: {at.exception}")
            tested.append(page)

        for week in range(1, 15):
            at = AppTest.from_file(str(REPO_ROOT / "app.py"))
            at.session_state["auth_ok"] = True
            at.session_state["role"] = "admin"
            at.session_state["nav_page"] = "📋 커리큘럼"
            at.session_state["cur_selected_id"] = COURSE_ID
            at.session_state["cur_selected_week"] = week
            at.run(timeout=45)
            if at.exception:
                raise AssertionError(
                    f"AppTest failed for course week {week} study mode: {at.exception}"
                )
            tested.append(f"커리큘럼 {week}강 공부 모드")
    finally:
        storage.DATA_ROOT = original_root
        storage._BACKEND = original_backend
    return tested


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--skip-app", action="store_true")
    args = parser.parse_args()
    data_root = args.data_root.resolve()

    try:
        report = {"status": "passed", "data": verify_data(data_root)}
        if not args.skip_app:
            report["app_pages"] = verify_app(data_root)
    except (AssertionError, FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "status": "failed",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
