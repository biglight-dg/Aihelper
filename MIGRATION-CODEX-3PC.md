# 3PC Codex 전환 및 클론 가이드

## 운영 기준

- 메인 에이전트는 **Codex**다. 각 저장소의 `AGENTS.md`를 지침으로 사용한다.
- GitHub 저장소는 `biglight-dg/Aihelper`, `biglight-dg/invest-assistant`다.
- `harry_potter-game`은 로컬 전용이며 GitHub에 올리거나 다른 PC에 클론하지 않는다.
- 세 PC가 같은 공유드라이브 데이터를 사용하므로 예약 자동화는 한 대에서만 실행한다.

## 표준 폴더 구조

```text
C:\Users\<user>\Codex\
├─ AGENTS.md
└─ Projects\
   ├─ Aihelper\             # GitHub: biglight-dg/Aihelper
   ├─ invest-assistant\     # GitHub: biglight-dg/invest-assistant
   └─ harry_potter-game\    # 주 PC 로컬 전용, GitHub 없음
```

새 PC의 사용자명이 다르면 `<user>` 부분만 바꾼다. 저장소 내부 스크립트는
가능한 한 현재 저장소 위치를 기준으로 경로를 계산하므로 사용자명에 의존하지 않는다.

## 새 PC 설치

```powershell
New-Item -ItemType Directory -Force "$HOME\Codex\Projects"
Set-Location "$HOME\Codex\Projects"
git clone https://github.com/biglight-dg/Aihelper.git Aihelper
git clone https://github.com/biglight-dg/invest-assistant.git invest-assistant
```

필수 프로그램:

- Git
- Python 3.12
- Node.js
- Codex CLI 로그인
- Google Drive for desktop

Aihelper 준비:

```powershell
Set-Location "$HOME\Codex\Projects\Aihelper"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 공유 데이터 정션

`data/`의 실제 원본은 다음 공유드라이브 경로다. 폴더명은 외부 자원이라 유지한다.

```text
G:\공유 드라이브\Chapterkorean-claude-cowork\claudehelper\data
```

클론 직후 `data`가 없을 때만 연결한다.

```powershell
New-Item -ItemType Junction `
  -Path "$HOME\Codex\Projects\Aihelper\data" `
  -Target "G:\공유 드라이브\Chapterkorean-claude-cowork\claudehelper\data"
```

확인:

```powershell
Get-Item "$HOME\Codex\Projects\Aihelper\data" |
  Select-Object FullName,LinkType,Target
```

## PC별 시크릿

GitHub에서 내려오지 않으므로 기존 PC에서 안전한 방법으로 별도 전달한다.

- `Aihelper\.env`
- `Aihelper\secrets\gcp_service_account.json`
- `Aihelper\.streamlit\secrets.toml`이 필요한 경우
- `invest-assistant\config\sources.json` 또는 `OPENDART_API_KEY`, `FRED_API_KEY`

시크릿 파일을 커밋하거나 채팅·메신저에 평문으로 남기지 않는다.

## 자동화 담당 PC

한 대만 자동화 담당으로 지정하고 다음을 실행한다.

```powershell
Set-Location "$HOME\Codex\Projects\Aihelper"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\register_tasks.ps1

Set-Location "$HOME\Codex\Projects\invest-assistant"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\register-tasks.ps1
```

나머지 두 PC에는 예약 작업을 등록하지 않는다. 수동 실행과 Streamlit 앱 사용만 한다.

invest-assistant의 Notion 연결은 자동화 담당 PC에서 별도로 인증한다.

```powershell
codex mcp add notion_remote --url https://mcp.notion.com/mcp
codex mcp login notion_remote
```

## 기존 Claude 폴더 정리

각 PC에서 Codex 클론과 실행 검증을 끝낸 뒤 진행한다.

1. 기존 Claude 저장소에서 `git status`를 확인하고 필요한 변경을 먼저 push한다.
2. `.env`, `secrets/`, 로컬 전용 파일을 Codex 저장소로 안전하게 옮긴다.
3. Codex 경로에서 앱 실행, 공유드라이브 정션, Git 원격을 확인한다.
4. 기존 Claude 예약 작업을 제거하고 Codex 경로의 작업만 등록한다.
5. 기존 폴더를 즉시 삭제하지 말고 `_archive` 이름으로 변경해 7일간 보관한다.
6. 데이터 정션은 실제 공유드라이브 폴더와 다르다. 정션 여부를 확인하지 않고
   공유드라이브 원본을 삭제하지 않는다.
7. 7일 동안 누락이 없음을 확인한 뒤 Claude 쪽 프로젝트 복사본만 정리한다.

검증 명령:

```powershell
git -C "$HOME\Codex\Projects\Aihelper" remote -v
git -C "$HOME\Codex\Projects\Aihelper" status
git -C "$HOME\Codex\Projects\invest-assistant" remote -v
git -C "$HOME\Codex\Projects\invest-assistant" status
Get-Command codex
```
