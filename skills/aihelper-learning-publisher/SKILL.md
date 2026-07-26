---
name: aihelper-learning-publisher
description: Build, validate, and safely publish AIHelper learning delivery data from verified Phase 4 KPK, TIP, and CHK Markdown artifacts. Use when creating or refreshing the 14-domain curriculum, worked examples, practices, quizzes, checklist UI, tips catalog, slides, manifests, or handoff evidence without claiming that examples are verified project applications.
---

# AIHelper Learning Publisher

Turn the 42 verified Phase 4 source artifacts into the AIHelper course and learning-lab data. Preserve source traceability and existing unrelated data.

## Workflow

1. Read `AGENTS.md` and `directives/phase4-learning-assets.md` completely.
2. Confirm the data root, `knowledge_db.json` hash, and the presence of 14 verified files in each source folder:
   - `knowledge/phase4/packages`
   - `knowledge/phase4/tips`
   - `knowledge/phase4/checklists`
3. Run `scripts/build_phase4_learning_assets.py` without `--apply`.
4. Reject the build if the report is not exactly 14 sessions, 14 learning assets, and 14 Phase 4 tips.
5. Apply to an isolated data fixture and run:
   - Python syntax and unit tests
   - slide layout validation
   - Streamlit AppTest for Knowledge Base, Curriculum, Learning Lab, and Tips
6. Review the delivery contract for every module:
   - three observable objectives
   - one worked example
   - three practice steps
   - three check questions
   - checklist and hard stops
   - KPK, TIP, and CHK IDs and paths
7. Before production apply, preserve the generated targets under `data/backups/phase4-learning-activation-*`.
8. Apply once, verify the generated manifest hashes and UI counts, then report the backup path and Git state.

## Content Contract

Use the sequence `배우기 → 예시 → 해보기 → 통과`.

- Write for non-specialist beginner-to-intermediate learners.
- Explain unfamiliar terms with a concrete example.
- Use neutral instructional language; do not replace evidence or criteria with encouragement.
- Keep knowledge claims in the source Markdown. Delivery JSON summarizes and links to it.
- Treat hard stops as non-compensable. A high average score cannot override one.
- Preserve existing curricula and tips whose IDs are outside this Phase 4 package.

## Project-Evidence Boundary

Worked examples are teaching fixtures unless the underlying project source, build, or external state was directly observed. Do not describe a fixture as a completed, tested, or production-ready application of Chris's project.

Actual project application is a separate step. Wait until the user decides whether Claude or Codex owns that step.

## Stop Conditions

Stop and report instead of writing when:

- a source artifact is missing, duplicated, or not `verified`;
- the expected knowledge index hash differs;
- an isolated build or UI regression test fails;
- the target contains conflicting Phase 4 records that cannot be merged by stable ID;
- production application would modify files outside the declared generated targets.

## Handoff

Report the input hash, generated file hashes, 14/14/14 counts, test results, backup path, code commit, and production data verification. Keep the actual-project application decision explicitly pending.
