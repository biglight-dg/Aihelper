# Aihelper

AI 교육팀과 지식베이스를 위한 Python/Streamlit 앱입니다. 이 저장소의
오케스트레이션 주체는 **Codex**이며, 운영 지침은 `AGENTS.md`가 기준입니다.

- GitHub: `biglight-dg/Aihelper`
- Streamlit Cloud: https://learnai-biglight.streamlit.app/
- 표준 로컬 경로: `C:\Users\<user>\Codex\Projects\Aihelper`
- 3PC 설치/이전: `MIGRATION-CODEX-3PC.md`

## 로컬 실행

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start.bat
```

`data/`는 Git에 포함하지 않습니다. 운영 PC에서는 Google 공유드라이브의
기존 `claudehelper\data` 폴더를 정션으로 연결합니다. GCP 프로젝트 ID와
공유드라이브 폴더명에 남은 `claudehelper`는 외부 자원 식별자이므로 변경하지
않습니다.

## Codex 운영

- Codex는 `AGENTS.md`를 먼저 읽습니다.
- 주간 뉴스 자동화는 `tools/weekly_digest.ps1`이 `codex exec`를 호출합니다.
- 세 PC 중 한 대만 자동화 담당 PC로 지정합니다.
- `.env`, `secrets/`, `.streamlit/secrets.toml`은 PC별로 설정하며 Git에 올리지 않습니다.
