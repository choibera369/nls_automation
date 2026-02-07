@echo off
title NLS_Automation

:: Step 1: NLS Program Execute
cd /d "C:\Users\alex\AppData\Roaming\Roaming\18D-NLS"
echo Starting NLS Support Scripts...

for %%f in (*.bat) do (
    if /i not "%%~nxf"=="run_all.bat" if /i not "%%~nxf"=="run_nls.bat" (
        call "%%f"
    )
)

timeout /t 5 /nobreak >nul
start "" "the18dnls.exe"

:: Step 2: Python Automation Execute
echo.
echo Starting Python Automation...
cd /d "F:\claude\intellizen\nls_automation"
"C:\Users\alex\AppData\Local\Programs\Python\Python312\python.exe" nls_full_auto.py

pause