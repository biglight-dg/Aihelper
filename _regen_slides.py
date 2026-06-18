# -*- coding: utf-8 -*-
"""커리큘럼 슬라이드 재생성: build_slides_data → save_slides → PptxMaker PPTX.
인자로 커리큘럼 id를 받는다."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from tools.curriculum_tools import (
    load_curriculum_db, load_curriculum, save_slides, save_curriculum,
)
from agents.curriculum import build_slides_data
from agents.educator import Educator


def regen(curriculum_id: str):
    db = load_curriculum_db()
    entry = next(c for c in db["curricula"] if c["id"] == curriculum_id)
    cur = load_curriculum(entry["path"])

    slides = build_slides_data(cur)
    slides_path = save_slides(cur, slides)  # generated.slides_path + last_generated 갱신
    print("SLIDES_JSON:", slides_path)
    print("SLIDE_COUNT:", len(slides))

    # 타이틀 슬라이드의 부제(학습 경로 포함)를 그대로 사용
    subtitle = next((s.get("subtitle", "") for s in slides if s.get("type") == "title"),
                    cur.get("description", ""))
    pptx_path = Educator().make_pptx(
        cur["title"], subtitle, slides, source=cur.get("description", "AI 교육팀"),
    )
    cur["generated"]["pptx_path"] = pptx_path
    save_curriculum(cur)
    print("PPTX:", pptx_path)

    from pptx import Presentation
    prs = Presentation(pptx_path)
    print("PPTX_SLIDES:", len(prs.slides._sldIdLst))
    print("LAST_GENERATED:", cur["generated"]["last_generated"])


if __name__ == "__main__":
    regen(sys.argv[1])
