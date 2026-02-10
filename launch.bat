@echo off
:: 간단한 GUI 실행기 — UTF-8 콘솔로 설정하고 파이썬을 실행합니다.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

set SCRIPT=%~dp0source\main.py

goto run-gui

:run-gui
echo 실행 중...
python "%SCRIPT%"
if %ERRORLEVEL% EQU 0 (
	goto end
) else (
	echo [!] 프로그램 오류로 종료됨. 아무 키나 누르면 창이 닫힙니다.
	pause
)

:end
exit
