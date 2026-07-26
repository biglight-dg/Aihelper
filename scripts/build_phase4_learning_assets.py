"""Build the Phase 4 course, tips, practice cases, quizzes, and checklists.

The 42 verified Markdown artifacts remain the evidence layer. This script creates
deterministic delivery data that AIHelper can render without duplicating the
source knowledge by hand.

Dry-run is the default. Pass ``--apply`` only after the printed validation report
is clean. Existing unrelated curricula and tips are preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COURSE_ID = "cur_phase4_14_domain_foundations"
COURSE_PATH = "curricula/phase4-14-domain-foundations.json"
SLIDES_PATH = "curricula/phase4-14-domain-foundations_slides.json"
GENERATED_AT = "2026-07-25T00:00:00+09:00"


MODULE_SPECS = [
    {
        "category": "평가·품질",
        "part": "Part A · 판단과 안전",
        "title": "AI 결과를 검증하는 평가 설계",
        "summary": "좋아 보이는 결과가 아니라 대표 사례, 판정 기준, 치명적 실패, 운영 관측으로 AI 품질을 확인합니다.",
        "concepts": [
            ("평가셋", "정상·경계·위험 사례를 함께 둡니다.", "시험 문제 묶음처럼 실제 업무의 여러 경우를 대표합니다."),
            ("루브릭과 hard fail", "품질 점수와 절대 통과할 수 없는 실패를 분리합니다.", "평균이 높아도 개인정보 노출 한 번은 통과할 수 없습니다."),
            ("운영 피드백", "고정 시험과 실제 사용 결과를 따로 관측합니다.", "연습 시험 점수와 실제 경기 기록을 구분합니다."),
        ],
        "example": ("AI 강의 요약 QA", "출처가 있는 강의 요약 6개와 출처가 없거나 충돌하는 사례 4개", "각 사례에 필수 조건·금지 조건을 쓰고 개인정보 노출과 허위 출처를 hard fail로 둡니다.", "총점과 별도로 hard fail 여부, 판정 근거, 다음 운영 관측 항목을 남긴 평가 결과표"),
        "activities": ["반복 업무 하나의 정상·경계·위험 사례를 각각 2개 작성합니다.", "0~2점 루브릭 3개와 평균으로 상쇄할 수 없는 hard fail 3개를 정의합니다.", "고정 평가로 알 수 없는 운영 공백과 다음 관측 계획을 기록합니다."],
    },
    {
        "category": "안전·권한",
        "part": "Part A · 판단과 안전",
        "title": "에이전트 권한과 승인 경계",
        "summary": "외부 자료의 지시와 실제 전송·수정·삭제 권한 사이를 분리해 에이전트 사고를 막습니다.",
        "concepts": [
            ("source와 sink", "읽은 정보와 외부에 영향을 주는 행동을 구분합니다.", "메모를 읽는 일과 메일을 보내는 일은 같은 권한이 아닙니다."),
            ("권한 계약", "resource·verb·scope·data class·expiry·owner를 씁니다.", "열쇠마다 열 수 있는 문과 사용 기한을 붙이는 방식입니다."),
            ("승인과 증거", "실행 직전 행동 목록을 승인받고 실행 뒤 실제 상태를 확인합니다.", "주문서 확인과 배송 완료 확인을 따로 남깁니다."),
        ],
        "example": ("고객 문의 정리 에이전트", "비신뢰 고객 메일과 내부 답변 지침", "원문은 인용 데이터로만 보관하고, 답변 초안과 발송 행동을 분리하며 발송 전 수신자·본문·첨부를 승인받습니다.", "초안 JSON, 승인된 action manifest, 실제 발송 상태 또는 보류 사유"),
        "activities": ["업무 흐름에서 비신뢰 source와 고영향 sink를 표시합니다.", "필요한 권한을 resource·verb·scope·expiry 표로 만듭니다.", "승인 전 action manifest와 실행 후 외부 상태 확인 절차를 작성합니다."],
    },
    {
        "category": "프론트엔드",
        "part": "Part B · 만들기와 성장",
        "title": "AI와 만드는 프론트엔드 기초",
        "summary": "화면을 구조, 표현, 상태, 이벤트, 데이터 흐름으로 나누고 작은 기능을 브라우저에서 검증합니다.",
        "concepts": [
            ("semantic HTML", "내용의 역할을 태그 구조로 먼저 표현합니다.", "건물의 방 이름과 출입구를 먼저 정하는 일입니다."),
            ("state contract", "loading·empty·error·ready 상태를 명시합니다.", "맑음만 그리지 않고 비·눈·정전 상황도 준비합니다."),
            ("브라우저 검증", "키보드, 반응형, 오류 상태를 실제 화면에서 확인합니다.", "설계도뿐 아니라 완성된 문이 실제로 열리는지 확인합니다."),
        ],
        "example": ("출처 상태 카드", "제목, 상태, 출처 URL이 있는 작은 데이터 한 건", "HTML로 제목과 상태 영역을 만들고 CSS로 반응형 배치한 뒤 JavaScript로 loading·error·ready를 전환합니다.", "키보드로 읽을 수 있고 작은 화면에서도 넘치지 않으며 비신뢰 문자열을 textContent로 표시하는 카드"),
        "activities": ["사용자 결과 한 개와 acceptance 기준을 5줄 이내로 씁니다.", "JavaScript 없이 읽히는 semantic HTML과 responsive CSS를 만듭니다.", "loading·empty·error·ready 상태와 안전한 DOM 갱신을 구현하고 브라우저에서 확인합니다."],
    },
    {
        "category": "마케팅·성장",
        "part": "Part B · 만들기와 성장",
        "title": "AARRR 성장 지표와 실험",
        "summary": "퍼널 이름보다 사건, 분모, 기간, 코호트를 먼저 정의하고 병목 가설을 작은 실험으로 검증합니다.",
        "concepts": [
            ("metric contract", "entity·event·window·denominator를 한 줄에 고정합니다.", "점수판의 선수, 득점, 경기 시간, 출전 기준을 함께 적습니다."),
            ("cohort 병목", "같은 시작 조건의 집단에서 가장 큰 이탈을 가설로 봅니다.", "서로 다른 학년의 시험 점수를 한 표에서 섞지 않습니다."),
            ("experiment contract", "주 결과·안전 지표·판정 규칙을 실행 전에 씁니다.", "경기 뒤 규칙을 바꾸지 않도록 시작 전에 승리 조건을 정합니다."),
        ],
        "example": ("첫 수업 예약 퍼널", "광고 방문, 상담 신청, 첫 수업 예약 이벤트", "사용자와 7일 창을 고정하고 방문자를 분모로 activation을 계산한 뒤 가장 큰 이탈 구간에 한 가지 변경만 시험합니다.", "분모가 포함된 지표표, 병목 근거, primary outcome·guardrail·decision rule이 있는 실험 카드"),
        "activities": ["사업 한 개의 Acquisition부터 Revenue까지 metric contract를 씁니다.", "같은 cohort와 segment에서 병목 가설 하나를 선택합니다.", "한 가지 변경만 포함한 실험과 중단·채택 기준을 작성합니다."],
    },
    {
        "category": "SNS·콘텐츠",
        "part": "Part B · 만들기와 성장",
        "title": "SNS 콘텐츠 운영 시스템",
        "summary": "한 원자료의 주장과 근거를 보존하면서 채널별 변형, 권리, 게시 상태, 학습 기록을 연결합니다.",
        "concepts": [
            ("source atom", "원자료의 주장·근거·권리 상태를 한 단위로 저장합니다.", "여러 요리의 재료가 되는 손질된 기본 재료입니다."),
            ("channel variant", "같은 주장을 채널의 길이와 형식에 맞게 변환합니다.", "같은 내용을 포스터·라디오·설명서로 바꿉니다."),
            ("distribution learning", "게시 상태와 분모가 있는 성과를 다음 제작에 연결합니다.", "보낸 횟수보다 누가 보고 무엇을 했는지 기록합니다."),
        ],
        "example": ("TOPIK 학습 팁 재사용", "근거가 확인된 학습 팁 한 개와 사용 가능한 이미지", "핵심 claim과 proof를 고정하고 릴스·카루셀·블로그 버전으로 바꾸며 자막·권리·승인 상태를 기록합니다.", "세 가지 variant, 게시 ledger, 도달 대비 저장·클릭 지표와 다음 변경 한 줄"),
        "activities": ["재사용할 source atom 한 개의 claim·proof·rights를 기록합니다.", "릴스·카루셀·블로그용 variant를 각각 하나씩 설계합니다.", "caption·approval·publish state와 분모가 있는 성과 지표를 ledger에 연결합니다."],
    },
    {
        "category": "게임 개발",
        "part": "Part B · 만들기와 성장",
        "title": "게임 시스템과 playable slice",
        "summary": "캐릭터·아이템 목록보다 목표 경험, 핵심 루프, 행동 계약, 대응 가능성, 경제, 플레이테스트를 먼저 설계합니다.",
        "concepts": [
            ("경험과 core loop", "인지·결정·행동·규칙·피드백·재진입을 연결합니다.", "놀이가 반복될 때 매번 어떤 판단이 달라지는지 봅니다."),
            ("verb와 counterplay", "행동의 조건·비용·상태·효과·대응 방법을 씁니다.", "가위에는 바위라는 대응이 있어야 선택이 생깁니다."),
            ("경제와 playtest", "source·sink·stock을 작은 prototype에서 관찰합니다.", "수도꼭지와 배수구의 양을 실제 사용으로 확인합니다."),
        ],
        "example": ("한 방 전투 prototype", "마법사 1명, 적 2종, 자원 1개, 아이템 3개", "목표 경험과 핵심 결정 3개를 정하고 verb lifecycle·적 counterplay·자원 source/sink를 한 방에서만 구현합니다.", "graybox 범위, 역할 표, 행동 상태표, 아이템 계약, 설명 없는 player task와 사전 pass/fail"),
        "activities": ["목록형 게임 아이디어를 목표 경험·primary loop·non-goal로 바꿉니다.", "주인공 1명과 적 2종의 verb·resource·weakness·counterplay 표를 만듭니다.", "가장 위험한 가설을 한 room graybox와 blind playtest로 검증합니다."],
    },
    {
        "category": "강의·교육",
        "part": "Part C · 교육·언어·앱",
        "title": "수행 증거에서 역설계하는 강의",
        "summary": "목차보다 학습자가 혼자 수행해야 할 과제와 통과 증거를 먼저 정하고 설명·예시·연습·피드백을 맞춥니다.",
        "concepts": [
            ("수행 목표", "관찰 가능한 행동·조건·품질을 씁니다.", "안다 대신 도움 없이 표를 완성한다처럼 표현합니다."),
            ("정렬", "목표·평가·연습이 같은 수행 수준을 요구하게 합니다.", "수영을 평가하면서 책 읽기만 연습시키지 않습니다."),
            ("transfer", "도움을 줄인 뒤 새 상황에서도 수행하는지 확인합니다.", "예제의 숫자만 바꾸는 것이 아니라 다른 문제에 적용합니다."),
        ],
        "example": ("AI 프론트엔드 60분 모듈", "비전공 학습자가 상태 카드 한 개를 만들어야 하는 상황", "최종 독립 과제와 통과 기준을 먼저 만들고 완성 예시·부분 실습·무지원 실습 순서로 도움을 줄입니다.", "학습자 정의, 수행 목표, 평가표, 3단계 연습, 피드백 규칙, 지연 전이 확인"),
        "activities": ["기존 강의 목차에서 학습자와 실제 사용 장면을 한 문장으로 고정합니다.", "독립 수행 과제와 관찰 가능한 통과 기준을 먼저 만듭니다.", "완성 예시에서 무지원 수행으로 도움을 줄이는 3단계 연습을 설계합니다."],
    },
    {
        "category": "언어 학습",
        "part": "Part C · 교육·언어·앱",
        "title": "수행 성장 중심 언어 학습 프로그램",
        "summary": "학습량보다 실제 언어 과제, 지원 감소, 평가 타당성, 적응형 데이터 층을 중심으로 프로그램을 설계합니다.",
        "concepts": [
            ("communicative task", "누가 누구에게 무엇을 어떤 조건에서 전달하는지 씁니다.", "단어 암기량보다 실제 주문을 완료할 수 있는지 봅니다."),
            ("framework 경계", "CEFR·ACTFL·TOPIK의 목적과 기능을 섞지 않습니다.", "키와 몸무게를 같은 숫자라고 바로 환산하지 않습니다."),
            ("adaptive layers", "학습 event·상태 추정·추천·성과를 분리합니다.", "체온계, 진단, 처방, 회복 기록을 한 값으로 만들지 않습니다."),
        ],
        "example": ("한국 생활 민원 전화 모듈", "중급 학습자가 예약 변경을 전화로 요청해야 하는 상황", "필요 표현을 분석하고 모델·지원 연습·부분 지원·무지원 전화 과제를 거쳐 기능·정확성·상호작용을 평가합니다.", "한 주 task cycle, 수준 근거, 지원 단계, 평가 rubric, 개인정보를 제거한 학습 event"),
        "activities": ["실제 언어 task 한 개를 기능·조건·지원·품질 계약으로 씁니다.", "모델에서 무지원 수행까지 한 주 task cycle을 설계합니다.", "학습 event·상태 추정·추천·성과 데이터와 개인정보 경계를 나눕니다."],
    },
    {
        "category": "한국어 첨삭",
        "part": "Part C · 교육·언어·앱",
        "title": "근거 있는 AI 한국어 첨삭",
        "summary": "문장 전체를 임의로 바꾸지 않고 문제 범위, 근거, 수정안, 의미 보존, 사용자 결정을 기록합니다.",
        "concepts": [
            ("issue 분류", "문법·어휘·담화·스타일과 확실성을 구분합니다.", "고장 난 위치와 종류를 먼저 표시합니다."),
            ("edit ledger", "원문 범위·근거·수정안·상태를 한 변경 단위로 저장합니다.", "문서의 변경 이력을 줄 단위로 남깁니다."),
            ("meaning gate", "의미·목소리·학습 목적이 보존되는지 따로 확인합니다.", "맞춤법을 고치면서 글쓴이의 주장을 바꾸지 않습니다."),
        ],
        "example": ("TOPIK 쓰기 문장 첨삭", "학습자 원문과 과제 조건, 허용된 언어 자료", "문제 span을 표시하고 근거와 최소 수정안을 제안한 뒤 원문·교정본·자연스러운 대안·사용자 선택을 분리합니다.", "issue 목록, edit ledger, 의미 보존 결과, 수락·거절 이력, 사람 검토가 필요한 항목"),
        "activities": ["문장 한 개의 문제를 언어 층위·범위·근거·확실성으로 분해합니다.", "원문을 보존한 edit ledger와 최소 수정안을 작성합니다.", "의미·목소리 보존 gate와 수락·거절·에스컬레이션 상태를 검증합니다."],
    },
    {
        "category": "앱 개발",
        "part": "Part C · 교육·언어·앱",
        "title": "상태와 데이터로 설계하는 앱",
        "summary": "화면 목록보다 사용자 결과 하나의 vertical slice와 상태·데이터·권한·오프라인·출시 생명주기를 먼저 설계합니다.",
        "concepts": [
            ("vertical slice", "사용자 결과 하나가 UI부터 저장까지 끝까지 동작하게 합니다.", "케이크 한 층씩보다 모든 층이 보이는 한 조각을 먼저 만듭니다."),
            ("operational state", "loading·empty·offline·conflict·denied를 제품 상태로 봅니다.", "정상 도로뿐 아니라 공사·우회·막힘 표지도 설계합니다."),
            ("release evidence", "권한·개인정보·접근성·실기기 동작을 관찰해 출시를 판정합니다.", "상자 포장 완료가 아니라 실제 배송 도착까지 확인합니다."),
        ],
        "example": ("AI 첨삭 앱 한 조각", "문장 입력, 첨삭 요청, 결과 검토, 저장 흐름", "상태표와 데이터 소유권을 먼저 쓰고 offline queue·동의·오류·재시도를 포함한 한 흐름만 구현합니다.", "상태 전이표, 데이터 모델, 권한 화면, 실패 복구, 접근성·실기기·로그 검증 기록"),
        "activities": ["플랫폼 제약과 사용자 결과 한 개를 vertical slice로 정의합니다.", "loading·empty·offline·conflict·denied를 포함한 상태 전이표를 만듭니다.", "AI 실패·개인정보·접근성·실기기 검증을 포함한 release evidence를 작성합니다."],
    },
    {
        "category": "프로젝트 운영",
        "part": "Part D · 운영·사업·지식",
        "title": "검증 가능한 프로젝트 완료",
        "summary": "완료라는 말 대신 정본, acceptance, 실제 관측 상태, 복구, 인계 증거를 연결합니다.",
        "concepts": [
            ("canonical과 acceptance", "어디가 정본인지와 무엇을 보면 완료인지 먼저 씁니다.", "정답지 위치와 채점 기준을 시작 전에 고정합니다."),
            ("observed state", "명령 성공과 실제 파일·앱·원격 상태를 구분합니다.", "택배 접수와 수령 완료는 다른 상태입니다."),
            ("release와 handoff", "변경·검증·복구·다음 담당자의 재현 방법을 남깁니다.", "교대 일지에 현재 계기판과 다음 조작을 함께 적습니다."),
        ],
        "example": ("AIHelper 지식 배포", "코드 저장소와 공유 Drive 데이터가 함께 바뀌는 작업", "정본과 변경 범위를 선언하고 격리 테스트 후 코드 commit·데이터 hash·앱 화면을 각각 확인해 인계합니다.", "acceptance 목록, 변경 manifest, 테스트 결과, 외부 상태 hash, rollback 위치, 다음 담당자 명령"),
        "activities": ["업무 한 건의 정본·비정본·acceptance 기준을 작성합니다.", "실행 결과와 별도로 확인할 observed state를 목록화합니다.", "release evidence·rollback·다음 담당자의 재현 명령을 포함한 handoff를 만듭니다."],
    },
    {
        "category": "영업",
        "part": "Part D · 운영·사업·지식",
        "title": "고객 증거 중심 영업 pipeline",
        "summary": "발송 횟수나 감각적 점수보다 고객 적합성, 실제 진행 상태, 불확실성, 상호 약속을 기록합니다.",
        "concepts": [
            ("qualification", "고객 문제·권한·시기·제약을 fact·inference·unknown으로 나눕니다.", "관찰한 사실과 추측을 다른 칸에 적습니다."),
            ("customer stage", "우리 행동이 아니라 고객의 확인 가능한 진전으로 단계를 바꿉니다.", "제안서를 보냈다가 아니라 고객이 검토 일정을 확정했다를 씁니다."),
            ("mutual next step", "누가 무엇을 언제 할지 양쪽이 확인한 약속을 남깁니다.", "다시 연락이 아니라 담당자·행동·날짜가 있는 약속입니다."),
        ],
        "example": ("기업 한국어 교육 문의", "상담 메모, 참여 인원, 예산·일정의 미확인 항목", "사실과 추론을 분리하고 stage evidence를 확인한 뒤 고객과 우리 담당자의 다음 행동과 날짜를 합의합니다.", "opportunity 카드, 근거 있는 stage, 불확실성, 상호 next step, 개인정보 최소화 인계"),
        "activities": ["opportunity 한 건의 fit·intent·authority·timing을 fact·inference·unknown으로 나눕니다.", "현재 stage를 고객 행동 evidence로 다시 판정합니다.", "양쪽 담당자·행동·날짜가 있는 mutual next step과 인계 범위를 씁니다."],
    },
    {
        "category": "SEO·GEO",
        "part": "Part D · 운영·사업·지식",
        "title": "URL 상태와 사용자 가치로 운영하는 SEO",
        "summary": "페이지 수보다 각 URL의 의도, crawl·index·serve 상태, 원본 가치, 성과를 ledger로 연결합니다.",
        "concepts": [
            ("URL lifecycle", "발견·크롤·색인·제공 상태를 분리합니다.", "도서의 입고·분류·서가 배치·대출 가능을 나눕니다."),
            ("canonical과 가치", "대표 URL과 사용자가 얻는 원본 가치를 함께 확인합니다.", "같은 책의 복사본과 새 내용을 구분합니다."),
            ("outcome 측정", "노출·클릭·전환을 URL과 의도 단위로 연결합니다.", "사람이 길을 봤는지, 들어왔는지, 목적을 달성했는지 나눕니다."),
        ],
        "example": ("한국 생활 정보 URL 20개", "다국어 URL, canonical, sitemap, 검색 성과 표", "각 URL의 intent·language·crawl·index·serve·value 상태를 기록하고 중복과 미색인의 원인을 우선순위화합니다.", "URL state ledger, 기술·콘텐츠 원인 구분, 수정 batch, 검증 날짜, 사업 outcome 연결"),
        "activities": ["URL 20개의 intent·canonical·language·crawl·index·serve 상태를 기록합니다.", "기술 문제와 원본 가치 부족을 구분해 수정 batch를 정합니다.", "재검증 날짜와 노출·클릭·전환의 분모가 있는 결과를 연결합니다."],
    },
    {
        "category": "Second Brain",
        "part": "Part D · 운영·사업·지식",
        "title": "간단 메모를 영속 지식으로 승격하기",
        "summary": "원문 cue를 보존하면서 지식 유형, 근거, 정본, 연결, 최신성, 검색 질문을 갖춘 노트로 승격합니다.",
        "concepts": [
            ("provenance", "누가 언제 어떤 맥락에서 남겼는지 원문과 함께 보존합니다.", "사진을 자르더라도 원본과 촬영 정보를 남깁니다."),
            ("canonical note", "한 질문의 대표 노트와 연결 지도를 정합니다.", "같은 주소를 가리키는 대표 안내판을 둡니다."),
            ("retrieval과 freshness", "다시 찾을 질문과 재검토 조건으로 지식의 사용성을 확인합니다.", "창고에 넣는 것보다 필요할 때 찾고 유통기한을 확인합니다."),
        ],
        "example": ("게임 아이템 메모 승격", "'아이템 트리 필요'라는 한 줄 cue", "원문 cue를 보존하고 외부 조사 질문과 개인 결정 질문을 나눈 뒤 게임 시스템 노트와 연결하고 적용 조건을 씁니다.", "원문·해석·근거·적용 예시·한계·관련 노트·review_due·검색 질문이 있는 영속 노트"),
        "activities": ["cue 10개의 원문·작성 맥락·지식 유형을 보존합니다.", "각 cue를 외부 조사·개인 인터뷰·프로젝트 확인으로 라우팅합니다.", "정본 노트·관련 링크·freshness·retrieval 질문을 채우고 실제 검색으로 확인합니다."],
    },
]


def _parse_scalar(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [part.strip().strip("\"'") for part in body.split(",")]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the controlled frontmatter subset used by Phase 4 artifacts."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text

    meta: dict = {}
    active_key = None
    for line in lines[1:end]:
        if re.match(r"^\s+-\s+", line) and active_key:
            meta.setdefault(active_key, []).append(_parse_scalar(re.sub(r"^\s+-\s+", "", line)))
            continue
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            continue
        key, raw = match.groups()
        active_key = key
        meta[key] = _parse_scalar(raw) if raw else []
    return meta, "\n".join(lines[end + 1 :]).lstrip()


def _sections(text: str, level: int = 2) -> dict[str, str]:
    marker = "#" * level
    pattern = re.compile(rf"^{re.escape(marker)}\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    result = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip()] = text[start:end].strip()
    return result


def _find_section(sections: dict[str, str], prefix: str) -> str:
    prefix = prefix.lower()
    for title, body in sections.items():
        if title.lower().startswith(prefix):
            return body
    return ""


def _list_items(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        match = re.match(r"^\s*(?:[-*]\s+(?:\[[ xX]\]\s*)?|\d+[.)]\s+)(.+?)\s*$", line)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if value:
                items.append(value)
    return items


def _compact_markdown(text: str, limit: int = 520) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\^.+?\]", "", text)
    text = re.sub(r"[`*_>#|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _artifact(root: Path, folder: str, artifact_id: str) -> tuple[str, str, dict]:
    matches = sorted((root / "knowledge" / "phase4" / folder).glob(f"{artifact_id}*.md"))
    if len(matches) != 1:
        raise ValueError(f"{artifact_id}: expected one source file, found {len(matches)}")
    path = matches[0]
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    if meta.get("id") != artifact_id or meta.get("status") != "verified":
        raise ValueError(f"{artifact_id}: id/status validation failed")
    rel = path.relative_to(root).as_posix()
    return rel, body, meta


def _build_module(data_root: Path, number: int, spec: dict) -> tuple[dict, dict, dict]:
    suffix = f"{number:03d}"
    package_id = f"KPK-{number:04d}"
    tip_id = f"TIP-P4-{suffix}"
    checklist_id = f"CHK-P4-{suffix}"
    package_path, package_body, package_meta = _artifact(data_root, "packages", package_id)
    tip_path, tip_body, tip_meta = _artifact(data_root, "tips", tip_id)
    checklist_path, checklist_body, checklist_meta = _artifact(data_root, "checklists", checklist_id)

    practice_body = _find_section(_sections(package_body), "실습")
    practice_sections = _sections(practice_body, 3)
    deliverables = _list_items(_find_section(practice_sections, "산출물"))
    hard_stops = _list_items(_find_section(practice_sections, "hard fail"))
    rubric = _find_section(practice_sections, "rubric") or _find_section(practice_sections, "평가 rubric")

    tip_sections = _sections(tip_body)
    tip_action = _find_section(tip_sections, "행동")
    tip_example = _find_section(tip_sections, "예시") or _find_section(tip_sections, "기대 결과")
    if not tip_action:
        raise ValueError(f"{tip_id}: action section is missing")

    checklist_sections = _sections(checklist_body)
    checklist_items = []
    checklist_hard_stops = []
    for heading, section_body in checklist_sections.items():
        target = checklist_hard_stops if heading.lower().startswith("hard stop") else checklist_items
        for item in _list_items(section_body):
            target.append({"group": heading, "text": item})
    if not checklist_items or not checklist_hard_stops:
        raise ValueError(f"{checklist_id}: checklist or hard stop is missing")

    objectives = list(package_meta.get("learning_objectives") or [])
    if len(objectives) != 3:
        raise ValueError(f"{package_id}: expected exactly three learning objectives")

    concepts = [
        {"term": term, "explain": explain, "analogy": analogy}
        for term, explain, analogy in spec["concepts"]
    ]
    scenario, example_input, process, output = spec["example"]
    quizzes = [
        {
            "id": f"Q-P4-{suffix}-{idx}",
            "question": objective.replace("할 수 있다.", "하려면 무엇을 확인해야 하나요?"),
            "answer_guide": f"{concepts[idx - 1]['term']}: {concepts[idx - 1]['explain']}",
        }
        for idx, objective in enumerate(objectives, 1)
    ]

    asset = {
        "id": f"LRN-P4-{suffix}",
        "order": number,
        "title": spec["title"],
        "category": spec["category"],
        "part": spec["part"],
        "summary": spec["summary"],
        "status": "verified-source-derived",
        "source_artifacts": {
            "package": {"id": package_id, "path": package_path},
            "tip": {"id": tip_id, "path": tip_path},
            "checklist": {"id": checklist_id, "path": checklist_path},
        },
        "source_ids": package_meta.get("source_ids", []),
        "claim_ids": package_meta.get("claim_ids", []),
        "project_evidence": package_meta.get("project_evidence", []),
        "objectives": objectives,
        "concepts": concepts,
        "worked_example": {
            "title": scenario,
            "scenario": scenario,
            "input": example_input,
            "process": process,
            "output": output,
        },
        "practice": {
            "activities": spec["activities"],
            "deliverables": deliverables or spec["activities"],
            "rubric_markdown": rubric,
            "hard_stops": hard_stops,
        },
        "tip": {
            "title": tip_meta["title"],
            "body": _compact_markdown(tip_action),
            "example": _compact_markdown(tip_example),
        },
        "assessment": {
            "quiz": quizzes,
            "checklist_items": checklist_items,
            "hard_stops": checklist_hard_stops,
        },
    }

    session = {
        "id": f"ses_phase4_{number:02d}",
        "week": number,
        "title": spec["title"],
        "part": spec["part"],
        "category": spec["category"],
        "summary": spec["summary"],
        "objectives": objectives,
        "duration": "90분",
        "concepts": concepts,
        "knowledge_refs": [package_path],
        "tip_refs": [tip_path],
        "checklist_refs": [checklist_path],
        "learning_asset_id": asset["id"],
        "worked_example": asset["worked_example"],
        "activities": spec["activities"],
        "assessment": {
            "deliverables": asset["practice"]["deliverables"],
            "rubric_markdown": rubric,
            "quiz": quizzes,
            "checklist_items": checklist_items,
            "hard_stops": checklist_hard_stops,
        },
        "project_evidence": asset["project_evidence"],
        "references": [],
        "cross_refs": [],
        "notes": "각 단계의 산출물을 저장하고 통과 기준과 비교한 뒤 다음 단계로 이동합니다.",
    }

    tip_item = {
        "id": tip_id,
        "title": tip_meta["title"],
        "body": asset["tip"]["body"],
        "example": asset["tip"]["example"],
        "category": spec["category"],
        "tags": [spec["category"], package_id, checklist_id, "Phase 4"],
        "source": tip_path,
        "source_ids": tip_meta.get("source_ids", []),
        "claim_ids": tip_meta.get("claim_ids", []),
        "learning_asset_id": asset["id"],
        "added_at": GENERATED_AT,
        "updated_at": GENERATED_AT,
    }
    return asset, session, tip_item


def build_payloads(data_root: Path) -> dict[str, dict]:
    modules = [_build_module(data_root, index, spec) for index, spec in enumerate(MODULE_SPECS, 1)]
    assets = [item[0] for item in modules]
    sessions = [item[1] for item in modules]
    generated_tips = [item[2] for item in modules]

    curriculum = {
        "id": COURSE_ID,
        "title": "AI와 함께 일하는 14가지 실전 기초",
        "description": "비전공 초중급자가 AI 결과 평가부터 게임·강의·언어·앱·마케팅·프로젝트·지식 관리까지 실제 산출물과 통과 기준으로 배우는 14강 과정입니다.",
        "target_audience": "모든 분야의 비전공 초중급자",
        "track": "main",
        "order": 1,
        "level": "기초·실전",
        "prerequisites": [],
        "next": [],
        "created_at": GENERATED_AT,
        "updated_at": GENERATED_AT,
        "sessions": sessions,
        "generated": {
            "slides_path": SLIDES_PATH,
            "pptx_path": None,
            "last_generated": GENERATED_AT,
        },
    }

    current_curriculum_db = _read_json(data_root / "curricula" / "curriculum_db.json", {"curricula": []})
    curriculum_entry = {
        "id": COURSE_ID,
        "title": curriculum["title"],
        "path": COURSE_PATH,
        "track": "main",
        "order": 1,
        "level": "기초·실전",
    }
    curricula = [item for item in current_curriculum_db.get("curricula", []) if item.get("id") != COURSE_ID]
    curricula.append(curriculum_entry)
    curricula.sort(key=lambda item: (item.get("order") is None, item.get("order") or 999, item.get("title", "")))

    current_tips = _read_json(data_root / "ai_tips.json", {"items": []})
    tip_ids = {item["id"] for item in generated_tips}
    tips = [item for item in current_tips.get("items", []) if item.get("id") not in tip_ids]
    tips.extend(generated_tips)

    learning_assets = {
        "schema_version": "aihelper-learning-assets-v1",
        "course_id": COURSE_ID,
        "generated_at": GENERATED_AT,
        "flow": ["배우기", "예시", "해보기", "통과"],
        "items": assets,
    }
    return {
        COURSE_PATH: curriculum,
        "curricula/curriculum_db.json": {"curricula": curricula},
        "ai_tips.json": {"schema_version": "aihelper-tips-v1", "items": tips},
        "learning_assets.json": learning_assets,
    }


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_payloads(payloads: dict[str, dict]) -> list[str]:
    errors = []
    course = payloads[COURSE_PATH]
    assets = payloads["learning_assets.json"]["items"]
    tips = [item for item in payloads["ai_tips.json"]["items"] if str(item.get("id", "")).startswith("TIP-P4-")]
    if len(course.get("sessions", [])) != 14:
        errors.append("course must contain 14 sessions")
    if len(assets) != 14:
        errors.append("learning_assets must contain 14 items")
    if len(tips) != 14:
        errors.append("ai_tips must contain 14 Phase 4 tips")
    ids = {item["id"] for item in assets}
    if len(ids) != 14:
        errors.append("learning asset ids are not unique")
    for item in assets:
        if len(item.get("objectives", [])) != 3:
            errors.append(f"{item.get('id')}: objectives must contain 3 items")
        if not item.get("worked_example", {}).get("output"):
            errors.append(f"{item.get('id')}: worked example output is missing")
        if len(item.get("assessment", {}).get("quiz", [])) != 3:
            errors.append(f"{item.get('id')}: quiz must contain 3 questions")
        if not item.get("assessment", {}).get("hard_stops"):
            errors.append(f"{item.get('id')}: checklist hard stops are missing")
    return errors


def add_slides(payloads: dict[str, dict], source_root: Path) -> None:
    from agents.curriculum import build_slides_data, validate_slides_data
    from tools import storage

    original_root = storage.DATA_ROOT
    original_backend = storage._BACKEND
    try:
        storage.DATA_ROOT = source_root
        storage._BACKEND = None
        slides = build_slides_data(payloads[COURSE_PATH])
    finally:
        storage.DATA_ROOT = original_root
        storage._BACKEND = original_backend
    errors = validate_slides_data(slides)
    if errors:
        raise ValueError("slide validation failed: " + "; ".join(errors))
    payloads[SLIDES_PATH] = {
        "curriculum_title": payloads[COURSE_PATH]["title"],
        "generated_at": GENERATED_AT,
        "slides": slides,
    }


def _backup_targets(output_root: Path, targets: list[str]) -> Path | None:
    existing = [rel for rel in targets if (output_root / rel).exists()]
    if not existing:
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = output_root / "backups" / f"phase4-learning-activation-{stamp}"
    for rel in existing:
        destination = backup / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_root / rel, destination)
    return backup


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True, help="data root containing knowledge/phase4")
    parser.add_argument("--output-root", type=Path, help="data root to update; defaults to source root")
    parser.add_argument("--expected-knowledge-sha", help="optional sha256 guard for knowledge_db.json")
    parser.add_argument("--apply", action="store_true", help="write files after validation")
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output_root = (args.output_root or args.source_root).resolve()
    if args.expected_knowledge_sha:
        observed = _sha256((source_root / "knowledge_db.json").read_bytes())
        if observed.lower() != args.expected_knowledge_sha.lower():
            raise SystemExit(f"knowledge_db hash mismatch: {observed}")

    payloads = build_payloads(source_root)
    errors = validate_payloads(payloads)
    if errors:
        raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
    add_slides(payloads, source_root)

    manifest = {
        "schema_version": "phase4-learning-build-manifest-v1",
        "course_id": COURSE_ID,
        "source_root": str(source_root),
        "output_root": str(output_root),
        "counts": {"sessions": 14, "learning_assets": 14, "tips": 14},
        "files": {
            rel: {"sha256": _sha256(_json_bytes(payload)), "bytes": len(_json_bytes(payload))}
            for rel, payload in sorted(payloads.items())
        },
    }
    payloads["phase4-learning-manifest.json"] = manifest

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if not args.apply:
        print("DRY RUN - no files written")
        return 0

    backup = _backup_targets(output_root, list(payloads))
    for rel, payload in payloads.items():
        _atomic_write(output_root / rel, _json_bytes(payload))
    print(f"APPLIED - backup={backup if backup else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
