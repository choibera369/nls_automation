@echo off
chcp 65001 >nul
title NLS Capture Mode

:: ============================================
::  NLS 캡쳐 전용 모드
::  F9 = 21페이지 캡쳐, ESC = 종료
:: ============================================

cd /d "F:\claude\intellizen\nls_automation"

echo ============================================
echo  NLS 캡쳐 전용 모드
echo  F9  = 21페이지 캡쳐 시작
echo  ESC = 종료
echo ============================================
echo.

C:\Users\alex\AppData\Local\Programs\Python\Python312\python.exe nls_capture_hotkey.py

echo.
echo 프로그램이 종료되었습니다.
pause
