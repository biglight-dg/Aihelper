"""Build 14 independent domain curricula from the Phase 3 knowledge tree.

The source Markdown remains the knowledge layer. This builder copies the source
nodes into AIHelper, creates one lesson per node, generates current 4:5 slides,
adds learning-lab assets, and preserves unrelated curricula and data.

Dry-run is the default. Pass ``--apply`` only after an isolated fixture passes
``scripts/verify_domain_curricula.py`` and the existing Phase 4 verifier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.curriculum import build_slides_data, validate_slides_data
from tools import storage


GENERATED_AT = "2026-07-28T00:00:00+09:00"
DOMAIN_MANIFEST_REL = "domain-curricula-manifest.json"


DOMAIN_SPECS = (
    {
        "id": "00", "slug": "quality-foundations", "category": "평가·품질",
        "title": "AI 품질·근거 공통 기반",
        "description": "사실·추론·권장·가설을 구분하고 출처·충돌·최신성을 검증하는 공통 기초 과정입니다.",
    },
    {
        "id": "01", "slug": "game-development", "category": "게임 개발",
        "title": "AI와 함께하는 게임 개발",
        "description": "목표 경험과 핵심 루프부터 캐릭터·아이템·장르·프로토타입·플레이테스트까지 연결합니다.",
    },
    {
        "id": "02", "slug": "product-frontend", "category": "프론트엔드",
        "title": "제품·프론트엔드 설계",
        "description": "사용자 문제와 비목표를 정의하고 상태·접근성·반응형·국제화를 제품 구조로 설계합니다.",
    },
    {
        "id": "03", "slug": "marketing-growth", "category": "마케팅·성장",
        "title": "마케팅 전략과 성장 측정",
        "description": "시장·고객·대안에서 포지셔닝·offer·구매 경로·성장 지표까지 검증 가능한 흐름으로 만듭니다.",
    },
    {
        "id": "04", "slug": "sns-content", "category": "SNS·콘텐츠",
        "title": "SNS·콘텐츠 제작 시스템",
        "description": "대상·약속·hook·payoff·CTA를 설계하고 플랫폼별 형식과 권리·성과 검증을 연결합니다.",
    },
    {
        "id": "05", "slug": "course-design", "category": "강의·교육",
        "title": "강의·교육 콘텐츠 설계",
        "description": "학습자 수행에서 목표·설명·연습·피드백·평가·전이를 역설계합니다.",
    },
    {
        "id": "06", "slug": "ai-agents", "category": "안전·권한",
        "title": "AI 자동화·에이전트 설계",
        "description": "script·workflow·agent 선택부터 권한·평가·재시도·rollback까지 안전한 실행 구조를 만듭니다.",
    },
    {
        "id": "07", "slug": "project-operations", "category": "프로젝트 운영",
        "title": "프로젝트·제품 운영",
        "description": "요구사항·인수 기준·정본·역할·위험·incident·handoff를 검증 가능한 상태 전이로 관리합니다.",
    },
    {
        "id": "08", "slug": "sales-business", "category": "영업",
        "title": "영업·고객·사업 설계",
        "description": "ICP·qualification·discovery부터 pipeline·exit criteria·forecast·follow-up까지 고객 증거로 운영합니다.",
    },
    {
        "id": "09", "slug": "seo-distribution", "category": "SEO·GEO",
        "title": "검색·SEO·콘텐츠 배포",
        "description": "검색 의도부터 crawl·index·serve·convert와 배포·canonical·재활용·retention을 연결합니다.",
    },
    {
        "id": "10", "slug": "second-brain", "category": "Second Brain",
        "title": "Second Brain 지식 운영",
        "description": "수집·정제·연결·검색·적용·검토·폐기와 cue 승격을 재현 가능한 지식 생명주기로 만듭니다.",
    },
    {
        "id": "11", "slug": "language-learning", "category": "언어 학습",
        "title": "언어 학습 프로그램 설계",
        "description": "언어 능력 모델·습득 가설·평가 타당성·적응형 상태·추천을 실제 수행 성장으로 연결합니다.",
    },
    {
        "id": "12", "slug": "korean-correction", "category": "한국어 첨삭",
        "title": "AI 한국어 첨삭 프로그램 설계",
        "description": "한국어 규범·오류 분류·규칙·LLM·의미 보존·corpus·blind review를 근거 있는 편집 제안으로 만듭니다.",
    },
    {
        "id": "13", "slug": "app-development", "category": "앱 개발",
        "title": "앱 개발 생명주기",
        "description": "플랫폼 선택·UI/domain/data/state 구조·보안·개인정보·계정 생명주기를 하나의 작동 경로로 설계합니다.",
    },
)


LEGACY_COURSE_META = {
    "cur_20260612_211500": {"track": "main", "order": 1, "level": "기초"},
    "cur_20260613_100001": {"track": "main", "order": 2, "level": "실전"},
    "cur_20260613_100010": {"track": "main", "order": 3, "level": "안전"},
    "cur_20260613_100013": {"track": "main", "order": 4, "level": "자동화"},
    "cur_20260613_100004": {"track": "elective", "order": 1, "level": "개발 교양"},
    "cur_20260612_203936": {"track": "elective", "order": 2, "level": "콘텐츠 제작"},
}


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clean_markdown(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", value)
    value = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), value)
    value = value.replace("**", "").replace("__", "")
    return re.sub(r"\s+", " ", value).strip(" -\n\t")


def _frontmatter_value(text: str, key: str, default: str = "") -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\n\"']+)", text)
    return match.group(1).strip() if match else default


def _frontmatter_list(text: str, key: str) -> list[str]:
    inline = re.search(rf"(?m)^{re.escape(key)}:\s*\[([^\]]*)\]", text)
    if inline:
        return [part.strip(" \"'") for part in inline.group(1).split(",") if part.strip()]
    block = re.search(rf"(?ms)^{re.escape(key)}:\s*\n((?:\s+-\s+[^\n]+\n?)+)", text)
    if not block:
        return []
    return [item.strip(" \"'") for item in re.findall(r"(?m)^\s+-\s+(.+)$", block.group(1))]


def _heading_title(text: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+)$", text)
    return _clean_markdown(match.group(1)) if match else fallback


def _section(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)", text)
    return match.group(1).strip() if match else ""


def _abstract(text: str) -> str:
    match = re.search(r"(?ms)> \[!abstract\][^\n]*\n>\s*(.+?)(?=\n\n|\n##)", text)
    if match:
        return _clean_markdown(match.group(1))
    paragraphs = [
        _clean_markdown(block)
        for block in re.split(r"\n\s*\n", re.sub(r"(?ms)^---\n.*?\n---\n", "", text, count=1))
        if block.strip() and not block.lstrip().startswith(("#", "|", "```", ">"))
    ]
    return paragraphs[0] if paragraphs else "핵심 원리와 적용 경계를 확인합니다."


def _aihelper_fields(text: str) -> dict[str, str]:
    section = _section(text, "AIHelper 전환")
    fields = {}
    for key in ("설명", "실습", "체크리스트"):
        match = re.search(rf"(?m)^-\s*{key}:\s*(.+)$", section)
        fields[key] = _clean_markdown(match.group(1)) if match else ""
    return fields


def _performance_fields(text: str) -> tuple[str, str, list[str]]:
    section = _section(text, "검증과 수행평가")
    input_match = re.search(r"(?m)^-\s*입력:\s*(.+)$", section)
    task_match = re.search(r"(?m)^-\s*과제:\s*(.+)$", section)
    criteria = []
    in_criteria = False
    for line in section.splitlines():
        if re.match(r"^-\s*합격 기준:\s*$", line):
            in_criteria = True
            continue
        if in_criteria:
            match = re.match(r"^\s{2,}-\s+(.+)$", line)
            if match:
                criteria.append(_clean_markdown(match.group(1)))
            elif line.strip() and not line.startswith(" "):
                break
    return (
        _clean_markdown(input_match.group(1)) if input_match else "주어진 사례와 현재 상태",
        _clean_markdown(task_match.group(1)) if task_match else "핵심 원리를 적용한 산출물을 작성합니다.",
        criteria,
    )


def _concepts(text: str, summary: str) -> list[dict]:
    ignored = {
        "AIHelper 전환", "검증과 수행평가", "주장과 근거", "다음 질문", "관련 노트",
        "내부 근거", "연결", "조사 경로", "핵심 질문",
    }
    headings = re.findall(r"(?m)^##\s+(.+)$", text)
    concepts = []
    for heading in headings:
        clean_heading = _clean_markdown(heading)
        if clean_heading in ignored or clean_heading.startswith("관련"):
            continue
        body = _section(text, heading)
        body = re.sub(r"(?ms)```.*?```", "", body)
        candidates = [
            _clean_markdown(block)
            for block in re.split(r"\n\s*\n", body)
            if block.strip() and not block.lstrip().startswith(("|", ">", "```", "#"))
        ]
        explanation = next((item for item in candidates if item), summary)
        concepts.append({
            "term": clean_heading[:40],
            "explain": explanation[:180],
            "analogy": "판단 기준과 적용 경계를 함께 확인합니다.",
        })
        if len(concepts) == 3:
            break
    if not concepts:
        concepts.append({"term": "핵심 원리", "explain": summary[:180], "analogy": "근거와 결과물을 연결합니다."})
    return concepts


def _checklist_items(raw: str, criteria: list[str]) -> list[dict]:
    pieces = [
        _clean_markdown(item)
        for item in re.split(r"[·,]", raw)
        if _clean_markdown(item)
    ]
    checks = pieces or criteria
    return [{"group": "체크", "text": f"{item}을(를) 확인했다."} for item in checks[:10]]


def _node_record(path: Path, target_rel: str, text: str) -> dict:
    node_id = _frontmatter_value(text, "node_id") or f"MOC-{_frontmatter_value(text, 'category_id', 'XX')}"
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "title": _heading_title(text, path.stem),
        "path": target_rel,
        "tags": _frontmatter_list(text, "tags"),
        "created_at": _frontmatter_value(text, "created", "2026-07-25"),
        "id": node_id,
        "artifact_type": "knowledge",
        "status": _frontmatter_value(text, "status", "draft"),
        "checked_at": _frontmatter_value(text, "updated", "2026-07-25"),
        "review_due": _frontmatter_value(text, "next_review") or None,
        "source_ids": _frontmatter_list(text, "sources"),
        "claim_ids": sorted(set(re.findall(r"CLM-\d+", text))),
        "project_evidence": _frontmatter_list(text, "projects"),
        "content_hash": f"sha256:{content_hash}",
        "aliases": [],
        "visibility": "internal",
        "volatility": _frontmatter_value(text, "freshness", "unknown"),
        "domain_curriculum_source": True,
    }


def _session_from_node(
    spec: dict,
    week: int,
    node_path: Path,
    target_rel: str,
    text: str,
    phase4_session: dict,
    phase4_asset: dict,
) -> tuple[dict, dict]:
    node_id = _frontmatter_value(text, "node_id")
    title = _heading_title(text, node_path.stem)
    summary = _abstract(text)
    aihelper = _aihelper_fields(text)
    input_text, task, criteria = _performance_fields(text)
    concepts = _concepts(text, summary)

    explain_goal = aihelper.get("설명") or concepts[0]["term"]
    practice_goal = aihelper.get("실습") or task
    objectives = [
        f"{explain_goal}을(를) 자신의 말로 설명할 수 있다.",
        f"{practice_goal}을(를) 직접 수행할 수 있다.",
        "근거·가설·결과를 분리하고 통과 또는 보류 이유를 기록할 수 있다.",
    ]
    activities = [
        f"입력 '{input_text}'을(를) 기준으로 {task}",
        practice_goal,
        "자신의 프로젝트에 같은 기준을 적용하고 적용 전후 증거와 남은 공백을 기록합니다.",
    ]
    deliverables = [task] + criteria[:4]
    if len(deliverables) < 3:
        deliverables.extend(["판단 근거와 source 목록", "적용 전후 비교와 다음 검증 계획"])

    rubric = (
        "| 기준 | 0 | 1 | 2 |\n|---|---|---|---|\n"
        "| 원리 이해 | 용어만 나열 | 일부 관계 설명 | 조건·경계·실패까지 설명 |\n"
        "| 적용 | 예시 복사 | 유사 사례 적용 | 자신의 제약에 맞게 재설계 |\n"
        "| 근거 | 출처·관찰 없음 | 일부 근거 | 사실·추론·가설·결과를 추적 |\n"
        "| 검증 | 완료 주장만 있음 | 체크 일부 | 통과·보류·중단 기준과 증거가 있음 |"
    )
    quiz = []
    for index, objective in enumerate(objectives, 1):
        quiz.append({
            "id": f"Q-DOM-{spec['id']}-{week:02d}-{index}",
            "question": f"{title}에서 {objective.rstrip('.')} 위해 무엇을 확인해야 하나요?",
            "answer_guide": criteria[index - 1] if index - 1 < len(criteria) else concepts[min(index - 1, len(concepts) - 1)]["explain"],
        })
    checklist_items = _checklist_items(aihelper.get("체크리스트", ""), criteria)
    checklist_items.extend([
        {"group": "남길 evidence", "text": "사용한 source와 확인 시점을 기록했다."},
        {"group": "남길 evidence", "text": "산출물·판정·남은 공백을 저장했다."},
    ])
    hard_stops = [
        {"group": "Hard stop", "text": "검증되지 않은 주장이나 teaching fixture를 실제 성과로 표시했다."},
        {"group": "Hard stop", "text": "source·판정 근거·보류 조건 없이 완료 처리했다."},
        {"group": "Hard stop", "text": "실제 개인정보·고객 데이터·운영 자원을 승인 없이 실습에 사용했다."},
    ]
    assessment = {
        "deliverables": deliverables[:6],
        "rubric_markdown": rubric,
        "quiz": quiz,
        "checklist_items": checklist_items,
        "hard_stops": hard_stops,
    }
    worked_example = {
        "title": f"{title} 판단 카드",
        "scenario": f"{spec['category']} 업무에서 결정을 내려야 하는 상황",
        "input": input_text,
        "process": task,
        "output": criteria[0] if criteria else "판단 근거·산출물·다음 검증 계획이 분리된 결과표",
    }

    session_id = f"ses_domain_{spec['id']}_{week:02d}"
    asset_id = f"LRN-DOM-{spec['id']}-{week:02d}"
    source_artifacts = {
        "knowledge": {"id": node_id, "path": target_rel},
        "package": {"id": Path(phase4_session["knowledge_refs"][0]).stem.split(" — ")[0], "path": phase4_session["knowledge_refs"][0]},
        "tip": {"id": Path(phase4_session["tip_refs"][0]).stem.split(" — ")[0], "path": phase4_session["tip_refs"][0]},
        "checklist": {"id": Path(phase4_session["checklist_refs"][0]).stem.split(" — ")[0], "path": phase4_session["checklist_refs"][0]},
    }
    session = {
        "id": session_id,
        "week": week,
        "title": title,
        "category": spec["category"],
        "summary": summary,
        "objectives": objectives,
        "duration": "75분",
        "concepts": concepts,
        "knowledge_refs": [target_rel],
        "tip_refs": list(phase4_session.get("tip_refs", [])),
        "checklist_refs": list(phase4_session.get("checklist_refs", [])),
        "learning_asset_id": asset_id,
        "worked_example": worked_example,
        "activities": activities,
        "assessment": assessment,
        "project_evidence": _frontmatter_list(text, "projects"),
        "references": [],
        "cross_refs": [],
        "notes": "원문 지식의 경계와 수행평가를 확인한 뒤 자신의 프로젝트에 전이합니다.",
    }
    asset = {
        "id": asset_id,
        "order": week,
        "course_order": int(spec["id"]) + 1,
        "course_id": f"cur_domain_{spec['id']}",
        "course_title": spec["title"],
        "week": week,
        "title": title,
        "category": spec["category"],
        "part": spec["title"],
        "summary": summary,
        "status": "source-derived-review-required",
        "source_artifacts": source_artifacts,
        "source_ids": _frontmatter_list(text, "sources"),
        "claim_ids": sorted(set(re.findall(r"CLM-\d+", text))),
        "project_evidence": _frontmatter_list(text, "projects"),
        "objectives": objectives,
        "concepts": concepts,
        "worked_example": worked_example,
        "practice": {
            "activities": activities,
            "deliverables": deliverables[:6],
            "rubric_markdown": rubric,
            "hard_stops": [item["text"] for item in hard_stops],
        },
        "tip": dict(phase4_asset.get("tip", {})),
        "assessment": {
            "quiz": quiz,
            "checklist_items": checklist_items,
            "hard_stops": hard_stops,
        },
    }
    return session, asset


def _enrich_legacy_course(course: dict, meta: dict) -> dict:
    course = json.loads(json.dumps(course, ensure_ascii=False))
    course.update(meta)
    course.setdefault("prerequisites", [])
    course.setdefault("next", [])
    for session in course.get("sessions", []):
        objectives = list(session.get("objectives", []))
        activities = list(session.get("activities", []))
        session.setdefault("summary", objectives[0] if objectives else session.get("title", ""))
        concept_labels = ("핵심 원리", "적용 기준", "검증 습관")
        concept_captions = (
            "원리를 자신의 말로 설명할 수 있어야 적용 단계로 넘어갑니다.",
            "작은 입력과 결과물을 비교해 적용 여부를 확인합니다.",
            "출처·권한·결과를 다시 확인해야 완료입니다.",
        )
        concept_objectives = (objectives + [session.get("title", "강의 주제")] * 3)[:3]
        session.setdefault("concepts", [
            {
                "term": concept_labels[index],
                "explain": f"이 강에서는 다음을 다룹니다: {objective.rstrip('.')}.",
                "analogy": concept_captions[index],
            }
            for index, objective in enumerate(concept_objectives)
        ])
        session.setdefault("worked_example", {
            "title": f"{session.get('title', '강의')} 적용 예시",
            "scenario": "AI를 처음 배우는 실무자가 한 단계씩 결과물을 만드는 상황",
            "input": activities[0] if activities else "강의 주제와 자신의 업무 사례",
            "process": activities[1] if len(activities) > 1 else "핵심 원리를 작은 작업에 적용합니다.",
            "output": activities[2] if len(activities) > 2 else "확인 가능한 결과물과 다음 연습 계획",
        })
        hard_stops = [
            {"group": "Hard stop", "text": "출처나 실제 확인 없이 AI 답변을 사실로 확정했다."},
            {"group": "Hard stop", "text": "개인정보·운영 파일·외부 계정을 승인 없이 실습에 사용했다."},
        ]
        title = session.get("title", "강의 주제")
        first_objective = objectives[0] if objectives else title
        first_activity = activities[0] if activities else "강의 주제를 자신의 업무 사례에 적용한 결과물"
        session.setdefault("assessment", {
            "deliverables": activities[:3] or ["강의 주제 적용 결과물", "확인 기록"],
            "rubric_markdown": (
                "| 기준 | 0 | 1 | 2 |\n|---|---|---|---|\n"
                "| 이해 | 용어만 반복 | 예시 설명 | 자신의 업무에 적용 |\n"
                "| 실행 | 산출물 없음 | 일부 수행 | 결과물과 확인 기록 존재 |\n"
                "| 안전 | 확인 없음 | 일부 점검 | 출처·권한·개인정보 점검 |"
            ),
            "quiz": [
                {
                    "id": f"Q-{session.get('id', 'LEGACY')}-1",
                    "question": f"‘{first_objective}’의 핵심을 자신의 말로 설명하세요.",
                    "answer_guide": first_objective,
                },
                {
                    "id": f"Q-{session.get('id', 'LEGACY')}-2",
                    "question": f"{title}을 실제 업무에 적용할 때 먼저 만들 결과물은 무엇인가요?",
                    "answer_guide": first_activity,
                },
                {
                    "id": f"Q-{session.get('id', 'LEGACY')}-3",
                    "question": f"{title} 결과를 완료로 판단하기 전에 확인할 기준 두 가지는 무엇인가요?",
                    "answer_guide": "결과물이 요구사항을 충족하는지 확인하고 출처·권한·개인정보 위험을 점검합니다.",
                },
            ],
            "checklist_items": [
                {"group": "체크", "text": activity} for activity in activities[:3]
            ],
            "hard_stops": hard_stops,
        })
        session.setdefault("notes", "기존 AI 학습 내용을 현재 실습·검증·슬라이드 계약으로 제공합니다.")
    return course


def _build_outputs(source_tree: Path, data_root: Path, staging_root: Path) -> tuple[dict[str, bytes], dict]:
    outputs: dict[str, bytes] = {}
    copied_nodes: list[dict] = []
    new_index_items: list[dict] = []

    curriculum_db = _read_json(data_root / "curricula" / "curriculum_db.json", {"curricula": []})
    learning_db = _read_json(data_root / "learning_assets.json", {"schema_version": "aihelper-learning-assets-v1", "items": []})
    knowledge_db = _read_json(data_root / "knowledge_db.json", {"schema_version": "aihelper-knowledge-index-v2", "items": []})
    phase4_course = _read_json(data_root / "curricula" / "phase4-14-domain-foundations.json")
    phase4_assets = {
        item.get("category"): item
        for item in learning_db.get("items", [])
        if str(item.get("id", "")).startswith("LRN-P4-")
    }
    phase4_sessions = {item.get("category"): item for item in phase4_course.get("sessions", [])}

    domain_courses: list[dict] = []
    domain_assets: list[dict] = []
    domain_entries: list[dict] = []
    node_ids: set[str] = set()

    for spec in DOMAIN_SPECS:
        source_dir = next((path for path in source_tree.iterdir() if path.is_dir() and path.name.startswith(spec["id"] + "-")), None)
        if source_dir is None:
            raise FileNotFoundError(f"source domain missing: {spec['id']}")
        phase4_session = phase4_sessions.get(spec["category"])
        phase4_asset = phase4_assets.get(spec["category"])
        if phase4_session is None or phase4_asset is None:
            raise AssertionError(f"Phase 4 anchor missing: {spec['category']}")

        markdown_files = sorted(source_dir.glob("*.md"))
        node_files = []
        for source_path in markdown_files:
            text = source_path.read_text(encoding="utf-8")
            node_id = _frontmatter_value(text, "node_id")
            if node_id:
                node_files.append((node_id, source_path, text))
            target_rel = f"knowledge/domain-curricula/{spec['id']}/{source_path.name}"
            outputs[target_rel] = source_path.read_bytes()
            record = _node_record(source_path, target_rel, text)
            new_index_items.append(record)
            copied_nodes.append({"id": record["id"], "path": target_rel, "sha256": _sha256_bytes(outputs[target_rel])})

        node_files.sort(key=lambda item: item[0])
        sessions = []
        for week, (node_id, source_path, text) in enumerate(node_files, 1):
            if node_id in node_ids:
                raise AssertionError(f"duplicate node id: {node_id}")
            node_ids.add(node_id)
            target_rel = f"knowledge/domain-curricula/{spec['id']}/{source_path.name}"
            session, asset = _session_from_node(
                spec, week, source_path, target_rel, text, phase4_session, phase4_asset
            )
            sessions.append(session)
            domain_assets.append(asset)

        course_id = f"cur_domain_{spec['id']}"
        course_path = f"curricula/domain-{spec['id']}-{spec['slug']}.json"
        slides_path = f"curricula/domain-{spec['id']}-{spec['slug']}_slides.json"
        course = {
            "id": course_id,
            "title": spec["title"],
            "description": spec["description"],
            "target_audience": "비전공 초중급자·1인 빌더·기획자",
            "track": "domain",
            "order": int(spec["id"]) + 1,
            "level": "기초·실전",
            "prerequisites": ["cur_phase4_14_domain_foundations"],
            "next": [],
            "created_at": GENERATED_AT,
            "updated_at": GENERATED_AT,
            "sessions": sessions,
            "generated": {"slides_path": slides_path, "pptx_path": None, "last_generated": GENERATED_AT},
        }
        domain_courses.append(course)
        outputs[course_path] = _json_bytes(course)
        domain_entries.append({
            "id": course_id, "title": spec["title"], "path": course_path,
            "track": "domain", "order": int(spec["id"]) + 1, "level": "기초·실전",
        })

    # Slides need the copied knowledge Markdown available through storage.
    for rel, payload in outputs.items():
        if rel.startswith("knowledge/"):
            target = staging_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
    original_root, original_backend = storage.DATA_ROOT, storage._BACKEND
    try:
        storage.DATA_ROOT = staging_root
        storage._BACKEND = None
        for spec, course in zip(DOMAIN_SPECS, domain_courses):
            slides = build_slides_data(course)
            errors = validate_slides_data(slides)
            if errors:
                raise AssertionError(f"{course['id']} slide validation failed: {'; '.join(errors)}")
            outputs[f"curricula/domain-{spec['id']}-{spec['slug']}_slides.json"] = _json_bytes({
                "curriculum_id": course["id"], "generated_at": GENERATED_AT, "slides": slides,
            })
    finally:
        storage.DATA_ROOT, storage._BACKEND = original_root, original_backend

    # Upgrade the six recoverable legacy courses to current lesson and slide contracts.
    upgraded_legacy = []
    for entry in curriculum_db.get("curricula", []):
        meta = LEGACY_COURSE_META.get(entry.get("id"))
        if not meta:
            continue
        rel = storage.to_relpath(entry["path"])
        course_path = data_root / rel
        if not course_path.exists():
            raise FileNotFoundError(f"legacy course missing: {rel}")
        course = _enrich_legacy_course(_read_json(course_path), meta)
        slide_rel = storage.to_relpath(course.get("generated", {}).get("slides_path") or rel[:-5] + "_slides.json")
        course["generated"]["slides_path"] = slide_rel
        course["generated"]["last_generated"] = GENERATED_AT
        outputs[rel] = _json_bytes(course)
        original_root, original_backend = storage.DATA_ROOT, storage._BACKEND
        try:
            storage.DATA_ROOT = data_root
            storage._BACKEND = None
            slides = build_slides_data(course)
        finally:
            storage.DATA_ROOT, storage._BACKEND = original_root, original_backend
        errors = validate_slides_data(slides)
        if errors:
            raise AssertionError(f"{course['id']} legacy slide validation failed: {'; '.join(errors)}")
        outputs[slide_rel] = _json_bytes({"curriculum_id": course["id"], "generated_at": GENERATED_AT, "slides": slides})
        upgraded_legacy.append({"id": course["id"], "sessions": len(course.get("sessions", [])), "slides": len(slides)})
        entry.update(meta)
        entry["path"] = rel

    # Preserve unrelated records while replacing stable domain IDs.
    domain_ids = {entry["id"] for entry in domain_entries}
    merged_entries = [entry for entry in curriculum_db.get("curricula", []) if entry.get("id") not in domain_ids]
    merged_entries.extend(domain_entries)
    merged_entries.sort(key=lambda item: (
        {"main": 0, "domain": 1, "special": 2, "elective": 3}.get(item.get("track", "main"), 4),
        item.get("order") is None,
        item.get("order") or 999,
        item.get("title", ""),
    ))
    merged_curriculum_db = {"curricula": merged_entries}
    outputs["curricula/curriculum_db.json"] = _json_bytes(merged_curriculum_db)

    domain_asset_ids = {item["id"] for item in domain_assets}
    preserved_assets = [item for item in learning_db.get("items", []) if item.get("id") not in domain_asset_ids]
    merged_learning = dict(learning_db)
    merged_learning["items"] = preserved_assets + domain_assets
    merged_learning["domain_curricula_generated_at"] = GENERATED_AT
    outputs["learning_assets.json"] = _json_bytes(merged_learning)

    new_ids = {item["id"] for item in new_index_items}
    new_paths = {item["path"] for item in new_index_items}
    preserved_index = [
        item for item in knowledge_db.get("items", [])
        if item.get("id") not in new_ids and item.get("path") not in new_paths
    ]
    merged_knowledge = dict(knowledge_db)
    merged_knowledge["items"] = preserved_index + new_index_items
    merged_knowledge["domain_curricula_import"] = {
        "generated_at": GENERATED_AT,
        "source": "Chris Second Brain Phase 3 knowledge-tree",
        "nodes": len(node_ids),
        "navigation_mocs": len(new_index_items) - len(node_ids),
    }
    outputs["knowledge_db.json"] = _json_bytes(merged_knowledge)

    # Keep the Phase 4 manifest truthful for shared files changed by this builder.
    phase4_manifest = _read_json(data_root / "phase4-learning-manifest.json")
    if phase4_manifest:
        for rel in ("curricula/curriculum_db.json", "learning_assets.json"):
            phase4_manifest["files"][rel] = {
                "sha256": _sha256_bytes(outputs[rel]), "bytes": len(outputs[rel]),
            }
        outputs["phase4-learning-manifest.json"] = _json_bytes(phase4_manifest)

    generated_files = {
        rel: {"sha256": _sha256_bytes(payload), "bytes": len(payload)}
        for rel, payload in sorted(outputs.items())
        if rel != DOMAIN_MANIFEST_REL
    }
    manifest = {
        "schema_version": "aihelper-domain-curricula-manifest-v1",
        "generated_by": "scripts/build_domain_curricula.py",
        "apply": False,
        "generated_at": GENERATED_AT,
        "counts": {
            "domain_courses": len(domain_courses),
            "domain_sessions": len(node_ids),
            "domain_learning_assets": len(domain_assets),
            "source_nodes": len(node_ids),
            "source_mocs": len(new_index_items) - len(node_ids),
            "legacy_courses_upgraded": len(upgraded_legacy),
            "catalog_courses": len(merged_entries),
        },
        "domains": [
            {"id": course["id"], "title": course["title"], "sessions": len(course["sessions"])}
            for course in domain_courses
        ],
        "legacy_courses": upgraded_legacy,
        "source_artifacts": copied_nodes,
        "files": generated_files,
    }
    outputs[DOMAIN_MANIFEST_REL] = _json_bytes(manifest)
    return outputs, manifest


def _apply_outputs(outputs: dict[str, bytes], data_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = data_root / "backups" / f"domain-curricula-{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=False)
    existing = []
    created = []
    for rel in outputs:
        target = data_root / rel
        if target.exists():
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
            existing.append(rel)
        else:
            created.append(rel)
    (backup_root / "recovery.json").write_text(
        json.dumps({"existing": existing, "created": created}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for rel, payload in outputs.items():
        target = data_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".domain-build-tmp")
        temp.write_bytes(payload)
        os.replace(temp, target)
    return backup_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-tree", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source_tree = args.source_tree.resolve()
    data_root = args.data_root.resolve()

    with tempfile.TemporaryDirectory(prefix="aihelper-domain-curricula-") as temp:
        outputs, manifest = _build_outputs(source_tree, data_root, Path(temp))

    manifest["apply"] = bool(args.apply)
    outputs[DOMAIN_MANIFEST_REL] = _json_bytes(manifest)
    if not args.apply:
        # Windows terminals may still use CP949; escaped JSON keeps dry-run output portable.
        print(json.dumps(manifest, ensure_ascii=True, indent=2))
        print("DRY RUN - no files written")
        return 0

    backup = _apply_outputs(outputs, data_root)
    # Windows terminals may still use CP949; escaped JSON keeps dry-run output portable.
    print(json.dumps(manifest, ensure_ascii=True, indent=2))
    print(f"APPLIED - backup={backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
