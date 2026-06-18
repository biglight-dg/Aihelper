@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem ── 지식 베이스 앱을 켜고, 외부 공유용 임시 주소(Cloudflare 터널)를 만든다 ──
rem  - 앱: Streamlit (127.0.0.1:8501, 터널을 통해서만 외부 접근)
rem  - 비밀번호: .streamlit\secrets.toml (공유 전에 꼭 바꾸기)
rem  - 이 창을 닫으면 공유가 종료됩니다.

set "PY=C:\Users\chris\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "CF=C:\Users\chris\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"

echo [1/2] 앱을 켜는 중...
start "지식베이스앱" /min cmd /c ""%PY%" -m streamlit run app.py --server.headless true"

echo      앱이 준비될 때까지 잠시 기다립니다...
timeout /t 7 /nobreak >nul

echo.
echo ============================================================
echo  [2/2] 공유 주소를 만드는 중...
echo  잠시 뒤 아래에 표시되는
echo      https://....trycloudflare.com
echo  주소를 지인에게 보내세요. (비밀번호는 secrets.toml 값)
echo.
echo  * 이 창을 닫으면 공유가 종료됩니다.
echo  * 주소는 켤 때마다 새로 바뀝니다(임시 터널).
echo ============================================================
echo.

"%CF%" tunnel --url http://localhost:8501

echo.
echo 공유를 종료합니다. 앱도 함께 종료합니다...
taskkill /F /T /FI "WINDOWTITLE eq 지식베이스앱*" >nul 2>&1
echo 완료. 이 창을 닫아도 됩니다.
pause
