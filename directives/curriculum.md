# Codex 커리큘럼 관리

`tools/curriculum_tools.py`와 `agents/curriculum.py`를 사용해 커리큘럼을 관리한다.

## 현황 확인

먼저 `data/curricula/curriculum_db.json`을 읽어 현재 커리큘럼 목록을 출력하라.
파일이 없으면 "아직 커리큘럼이 없습니다."라고 알린다.

## 명령어 목록

```
[제목] 커리큘럼 만들어줘
  → new_curriculum(title) + save_curriculum()

[N]강 세션 추가: [제목]
  → new_session(week=N, title) + sessions.append() + save_curriculum()
  (※ week 파라미터/필드는 내부 식별자로 유지, 사용자 표기는 "N강")

[N]강에 [파일명] 연결해줘
  → data/knowledge/ 에서 파일 검색 후 knowledge_refs 추가

[N]강 목표 바꿔줘: [목표]
  → 해당 세션 objectives 수정 + save_curriculum()

[N]강 활동 추가: [활동]
  → activities 추가 + save_curriculum()

[N]강 삭제해줘
  → sessions에서 제거 + save_curriculum()

커리큘럼 슬라이드 업데이트해줘
  → build_slides_data() → save_slides() (화면 슬라이드 JSON 재생성, PPTX 생성 안 함)

커리큘럼 목록 보여줘
  → curriculum_db.json 읽어서 목록 출력

[제목] 커리큘럼 삭제해줘
  → delete_curriculum(id)
```

## 작업 후 항상

- `save_curriculum(curriculum)` 호출 확인 (updated_at 자동 갱신)
- 변경 내용 요약 출력
- 슬라이드가 오래됐으면 "슬라이드 업데이트가 필요합니다." 안내

## 구조화 학습 자료가 연결된 강

Phase 4처럼 `learning_asset_id`가 있는 세션은 일반 세션 필드에 아래 계약을 추가한다.

- `tip_refs`: 바로 쓰는 팁 Markdown 경로
- `checklist_refs`: 실행 전·후 checklist Markdown 경로
- `worked_example`: 상황·입력·처리·결과가 있는 예시
- `assessment`: 제출물·rubric·확인 문제·checklist·hard stop

이 세션을 수정할 때는 `directives/phase4-learning-assets.md`를 함께 읽고,
`KPK/TIP/CHK` ID와 원문 경로를 보존한 채 슬라이드와 `learning_assets.json`을 같이 재검증한다.
