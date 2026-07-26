# Phase 4 학습 자료 생성·배포 지시서

## 목적

검증된 Phase 4 원문 42개를 AIHelper의 실제 학습 화면으로 변환한다.

- 지식 패키지 14개: 설명과 근거
- 꿀팁 14개: 바로 적용할 행동
- 체크리스트 14개: 실행 전·후 검사와 hard stop
- 전달 형식: `배우기 → 예시 → 해보기 → 통과`

원문 Markdown은 근거 계층으로 유지한다. 커리큘럼·실습·퀴즈 데이터는 원문을 대체하지 않으며 항상 `KPK/TIP/CHK` ID와 경로를 보존한다.

## 정본과 생성물

| 역할 | 경로 | 규칙 |
|---|---|---|
| 원문 정본 | `data/knowledge/phase4/{packages,tips,checklists}` | 직접 덮어쓰지 않는다 |
| 과정 | `data/curricula/phase4-14-domain-foundations.json` | 안정 ID로 갱신한다 |
| 슬라이드 | `data/curricula/phase4-14-domain-foundations_slides.json` | 과정 변경 뒤 재생성한다 |
| 꿀팁 UI | `data/ai_tips.json` | `TIP-P4-*`만 upsert하고 다른 팁은 보존한다 |
| 실습 UI | `data/learning_assets.json` | 14개 module을 구조화한다 |
| 배포 기록 | `data/phase4-learning-manifest.json` | 파일별 hash와 수량을 남긴다 |

## 생성 절차

1. `knowledge_db.json`의 기대 hash와 Phase 4 원문 42개의 존재·ID·`verified` 상태를 확인한다.
2. 실제 데이터가 아닌 격리된 data fixture에서 먼저 실행한다.
3. 아래 명령을 `--apply` 없이 실행해 수량과 파일 hash를 확인한다.

```powershell
python scripts/build_phase4_learning_assets.py `
  --source-root <DATA_ROOT> `
  --output-root <FIXTURE_ROOT>
```

4. dry-run 결과가 정상이면 fixture에 `--apply`하고 unit test, slide validation, Streamlit AppTest를 실행한다.
5. 실제 data root에 적용하기 전에 생성 대상 기존 파일을 같은 data root의 `backups/phase4-learning-activation-*` 아래에 복사한다.
6. 실제 적용 후 manifest hash, 과정 14강, 팁 14개, 실습 자료 14개, 앱 화면을 다시 확인한다.

## 필수 품질 기준

- 비전공 초중급자가 이해할 수 있는 문장과 구체적인 예시가 있다.
- 감정적 격려 문구로 설명이나 판정 기준을 대체하지 않는다.
- 세션마다 학습 목표 3개, worked example 1개, 실습 3개, 확인 문제 3개가 있다.
- 세션마다 관련 KPK·TIP·CHK 경로가 모두 연결된다.
- checklist의 hard stop이 평균 점수나 완료 체크로 상쇄되지 않는다.
- 슬라이드는 1280×1600, 4:5 규칙과 기존 layout validator를 통과한다.
- 실제 프로젝트에 적용했다는 표현은 프로젝트 원본·build·운영 상태를 관찰한 뒤에만 사용한다.

## 변경 경계

- 생성 스크립트는 다른 커리큘럼과 Phase 4가 아닌 기존 팁을 삭제하지 않는다.
- 프로젝트 적용, 외부 발송, 공개 게시, 결제, 개인정보 사용은 이 지시서의 범위가 아니다.
- 6단계 실제 프로젝트 적용 담당을 Claude 또는 Codex로 정하기 전에는 학습 자료의 예시를 실제 프로젝트 검증 결과로 표시하지 않는다.

## 인계 시 보고

- 입력 `knowledge_db.json` hash
- 생성된 파일과 각 hash
- 14/14/14 수량 검사 결과
- slide validation과 AppTest 결과
- backup 경로
- 실제 data와 Git commit의 최종 상태
