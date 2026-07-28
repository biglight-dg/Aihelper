from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.curriculum import validate_slides_data
from scripts.build_phase4_learning_assets import build_payloads as rebuild_phase4_payloads
from tools import storage
from tools.curriculum_tools import build_markdown_doc, build_session_doc


PHASE4_COURSE_ID = "cur_phase4_14_domain_foundations"
EXPECTED_COUNTS = {
    "domain_courses": 14,
    "domain_sessions": 42,
    "domain_learning_assets": 42,
    "source_nodes": 42,
    "source_mocs": 14,
    "legacy_courses_upgraded": 6,
    "catalog_courses": 21,
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_equal(observed, expected, label: str) -> None:
    if observed != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {observed!r}")


def verify_data(data_root: Path) -> dict:
    manifest = _read_json(data_root / "domain-curricula-manifest.json")
    _assert_equal(manifest.get("schema_version"), "aihelper-domain-curricula-manifest-v1", "manifest schema")
    _assert_equal(manifest.get("counts"), EXPECTED_COUNTS, "manifest counts")

    for rel, expected in manifest["files"].items():
        path = data_root / rel
        if not path.is_file():
            raise AssertionError(f"manifest target missing: {rel}")
        _assert_equal(_sha256(path), expected["sha256"], f"hash for {rel}")
        _assert_equal(path.stat().st_size, expected["bytes"], f"byte size for {rel}")

    catalog = _read_json(data_root / "curricula" / "curriculum_db.json").get("curricula", [])
    _assert_equal(len(catalog), EXPECTED_COUNTS["catalog_courses"], "catalog course count")
    catalog_ids = [item["id"] for item in catalog]
    _assert_equal(len(set(catalog_ids)), len(catalog_ids), "unique catalog ids")

    domain_specs = manifest["domains"]
    domain_ids = {item["id"] for item in domain_specs}
    legacy_ids = {item["id"] for item in manifest["legacy_courses"]}
    required_ids = domain_ids | legacy_ids | {PHASE4_COURSE_ID}
    missing_ids = required_ids - set(catalog_ids)
    if missing_ids:
        raise AssertionError(f"catalog is missing required courses: {sorted(missing_ids)}")

    entries = {item["id"]: item for item in catalog}
    source_nodes = {
        item["id"]: item["path"]
        for item in manifest["source_artifacts"]
        if item["id"].startswith("KN-")
    }
    source_mocs = {
        item["id"]: item["path"]
        for item in manifest["source_artifacts"]
        if item["id"].startswith("MOC-")
    }
    _assert_equal(len(source_nodes), EXPECTED_COUNTS["source_nodes"], "source node manifest count")
    _assert_equal(len(source_mocs), EXPECTED_COUNTS["source_mocs"], "source MOC manifest count")

    node_ref_counts: Counter[str] = Counter()
    domain_session_count = 0
    slide_counts: dict[str, int] = {}
    for spec in domain_specs:
        entry = entries[spec["id"]]
        _assert_equal(entry.get("track"), "domain", f"{spec['id']} track")
        course = _read_json(data_root / entry["path"])
        sessions = course.get("sessions", [])
        _assert_equal(len(sessions), spec["sessions"], f"{spec['id']} session count")
        domain_session_count += len(sessions)
        for session in sessions:
            _assert_equal(len(session.get("objectives", [])), 3, f"{session['id']} objectives")
            _assert_equal(len(session.get("activities", [])), 3, f"{session['id']} activities")
            _assert_equal(len(session.get("assessment", {}).get("quiz", [])), 3, f"{session['id']} quiz")
            if not session.get("assessment", {}).get("hard_stops"):
                raise AssertionError(f"{session['id']} hard stops are missing")
            refs = session.get("knowledge_refs", [])
            matching = [ref for ref in refs if ref in source_nodes.values()]
            _assert_equal(len(matching), 1, f"{session['id']} source-node reference")
            node_ref_counts.update(matching)
            for ref_field in ("knowledge_refs", "tip_refs", "checklist_refs"):
                for rel in session.get(ref_field, []):
                    if not (data_root / rel).is_file():
                        raise AssertionError(f"{session['id']} broken {ref_field}: {rel}")

        slides_path = course.get("generated", {}).get("slides_path")
        if not slides_path:
            raise AssertionError(f"{spec['id']} slides_path is missing")
        slides = _read_json(data_root / slides_path).get("slides", [])
        errors = validate_slides_data(slides)
        if errors:
            raise AssertionError(f"{spec['id']} slide validation failed: {'; '.join(errors)}")
        slide_counts[spec["id"]] = len(slides)

        for session in (sessions[0], sessions[-1]):
            doc = build_session_doc(course, session)
            for label in ("학습 흐름", "작업 예시", "실습 안내", "통과 기준", "확인 문제"):
                if label not in doc:
                    raise AssertionError(f"{session['id']} textbook missing section: {label}")

    _assert_equal(domain_session_count, EXPECTED_COUNTS["domain_sessions"], "domain session total")
    _assert_equal(set(node_ref_counts), set(source_nodes.values()), "covered source nodes")
    if any(count != 1 for count in node_ref_counts.values()):
        duplicates = {path: count for path, count in node_ref_counts.items() if count != 1}
        raise AssertionError(f"source nodes must be covered exactly once: {duplicates}")

    for legacy_id in legacy_ids:
        entry = entries[legacy_id]
        course = _read_json(data_root / entry["path"])
        build_markdown_doc(course)
        slides_path = course.get("generated", {}).get("slides_path")
        slides = _read_json(data_root / slides_path).get("slides", [])
        errors = validate_slides_data(slides)
        if errors:
            raise AssertionError(f"{legacy_id} upgraded slide validation failed: {'; '.join(errors)}")
        slide_counts[legacy_id] = len(slides)

    assets = _read_json(data_root / "learning_assets.json").get("items", [])
    domain_assets = [item for item in assets if str(item.get("id", "")).startswith("LRN-DOM-")]
    phase4_assets = [item for item in assets if str(item.get("id", "")).startswith("LRN-P4-")]
    _assert_equal(len(domain_assets), EXPECTED_COUNTS["domain_learning_assets"], "domain learning asset count")
    _assert_equal(len(phase4_assets), 14, "Phase 4 overview asset count")
    _assert_equal(len({item["id"] for item in assets}), len(assets), "unique learning asset ids")
    for asset in domain_assets:
        if asset.get("course_id") not in domain_ids:
            raise AssertionError(f"{asset['id']} has an unknown course_id")
        _assert_equal(len(asset.get("objectives", [])), 3, f"{asset['id']} objectives")
        _assert_equal(len(asset.get("assessment", {}).get("quiz", [])), 3, f"{asset['id']} quiz")
        if not asset.get("worked_example", {}).get("output"):
            raise AssertionError(f"{asset['id']} worked example output is missing")
        if not asset.get("practice", {}).get("activities"):
            raise AssertionError(f"{asset['id']} practice activities are missing")

    rebuilt_phase4 = rebuild_phase4_payloads(data_root)
    rebuilt_assets = rebuilt_phase4["learning_assets.json"].get("items", [])
    rebuilt_domain_ids = {
        item["id"] for item in rebuilt_assets if str(item.get("id", "")).startswith("LRN-DOM-")
    }
    _assert_equal(
        rebuilt_domain_ids,
        {item["id"] for item in domain_assets},
        "Phase 4 rebuild must preserve domain learning assets",
    )
    rebuilt_catalog_ids = {
        item["id"] for item in rebuilt_phase4["curricula/curriculum_db.json"].get("curricula", [])
    }
    if not required_ids.issubset(rebuilt_catalog_ids):
        raise AssertionError("Phase 4 rebuild would remove restored or domain curricula")

    knowledge_ids = {item.get("id") for item in _read_json(data_root / "knowledge_db.json").get("items", [])}
    missing_knowledge = (set(source_nodes) | set(source_mocs)) - knowledge_ids
    if missing_knowledge:
        raise AssertionError(f"knowledge_db is missing imported source ids: {sorted(missing_knowledge)}")

    return {
        "catalog_courses": len(catalog),
        "legacy_courses": len(legacy_ids),
        "overview_courses": 1,
        "domain_courses": len(domain_ids),
        "domain_sessions": domain_session_count,
        "learning_assets": len(assets),
        "knowledge_nodes": len(source_nodes),
        "knowledge_mocs": len(source_mocs),
        "slide_decks_validated": len(slide_counts),
        "slide_count": sum(slide_counts.values()),
        "phase4_rebuild_preserves_domain_assets": True,
    }


def _app_text(at) -> str:
    values = []
    for collection_name in ("title", "header", "subheader", "markdown", "caption", "button"):
        for element in getattr(at, collection_name, []):
            value = getattr(element, "value", None) or getattr(element, "label", None)
            if value:
                values.append(html.unescape(str(value)))
    return "\n".join(values)


def _new_app_test(page: str, *, course_id: str | None = None, week: int = 0):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(REPO_ROOT / "app.py"))
    at.session_state["auth_ok"] = True
    at.session_state["role"] = "admin"
    at.session_state["nav_page"] = page
    if course_id is not None:
        at.session_state["cur_selected_id"] = course_id
        at.session_state["cur_selected_week"] = week
    at.run(timeout=45)
    if at.exception:
        raise AssertionError(f"AppTest failed for {page}/{course_id}/{week}: {at.exception}")
    return at


def verify_app(data_root: Path) -> dict:
    manifest = _read_json(data_root / "domain-curricula-manifest.json")
    catalog = _read_json(data_root / "curricula" / "curriculum_db.json").get("curricula", [])
    entries = {item["id"]: item for item in catalog}
    original_root = storage.DATA_ROOT
    original_backend = storage._BACKEND
    rendered_lesson_modes = 0
    try:
        storage.DATA_ROOT = data_root
        storage._BACKEND = None

        dashboard = _new_app_test("📋 커리큘럼")
        dashboard_text = _app_text(dashboard)
        missing_titles = [item["title"] for item in catalog if item["title"] not in dashboard_text]
        if missing_titles:
            raise AssertionError(f"curriculum dashboard is missing titles: {missing_titles}")
        if "분야별 전문 과정" not in dashboard_text:
            raise AssertionError("curriculum dashboard is missing the domain-course section")

        learning_home = _new_app_test("🎓 학습 홈")
        learning_home_text = _app_text(learning_home)
        missing_home_titles = [
            item["title"] for item in manifest["domains"] if item["title"] not in learning_home_text
        ]
        if missing_home_titles:
            raise AssertionError(f"learning home is missing domain titles: {missing_home_titles}")

        _new_app_test("🧪 실습·체크")

        for spec in manifest["domains"]:
            course = _read_json(data_root / entries[spec["id"]]["path"])
            sessions = course["sessions"]
            for week in (0, sessions[0]["week"], sessions[-1]["week"]):
                at = _new_app_test("📋 커리큘럼", course_id=spec["id"], week=week)
                if course["title"] not in _app_text(at):
                    raise AssertionError(f"{spec['id']} title did not render for week {week}")
                rendered_lesson_modes += 1
    finally:
        storage.DATA_ROOT = original_root
        storage._BACKEND = original_backend

    return {
        "dashboard_courses_visible": len(catalog),
        "learning_home_domain_courses_visible": len(manifest["domains"]),
        "domain_course_modes_rendered": rendered_lesson_modes,
        "lab_rendered": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the restored and expanded AIHelper curriculum portfolio.")
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    result = {
        "status": "passed",
        "data": verify_data(data_root),
        "app": verify_app(data_root),
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
