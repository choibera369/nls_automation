"""
NLS Hotkey Launcher
Ctrl+Alt+N = NLS Auto Run
Shift+Ctrl+Alt+P = NLS Auto Run (alternative)
Ctrl+Alt+P = Patient App
"""

import subprocess
import os
import sys
import time
import ctypes
import logging
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "hotkey_launcher.log"),
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8"
)


def log(msg):
    logging.info(msg)


# Mutex - 중복 실행 방지
_mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "NLS_HOTKEY_LAUNCHER_MUTEX")
if ctypes.windll.kernel32.GetLastError() == 183:
    log("중복 실행 감지 → 종료")
    ctypes.windll.kernel32.CloseHandle(_mutex)
    sys.exit(1)

import keyboard

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
NLS_BAT = "NLS_Auto.bat"
PATIENT_BAT = "patient_app_run.bat"
COOLDOWN = 3.0

_last_nls_time = 0
_last_patient_time = 0
_nls_process = None


def launch_nls():
    global _last_nls_time, _nls_process
    if time.time() - _last_nls_time < COOLDOWN:
        log(f"Ctrl+Alt+N 무시 (쿨다운 {COOLDOWN}초)")
        return
    if _nls_process is not None and _nls_process.poll() is None:
        log("NLS Auto Run이 이미 실행 중 → 무시")
        return
    bat_path = os.path.join(DESKTOP, NLS_BAT)
    if not os.path.exists(bat_path):
        log(f"배치 파일 없음: {bat_path}")
        return
    _nls_process = subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    _last_nls_time = time.time()
    log("NLS Auto Run launched!")


def launch_patient():
    global _last_patient_time
    if time.time() - _last_patient_time < COOLDOWN:
        log(f"Ctrl+Alt+P 무시 (쿨다운 {COOLDOWN}초)")
        return
    bat_path = os.path.join(DESKTOP, PATIENT_BAT)
    if not os.path.exists(bat_path):
        log(f"배치 파일 없음: {bat_path}")
        return
    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    _last_patient_time = time.time()
    log("Patient App launched!")


keyboard.add_hotkey("ctrl+alt+n", launch_nls, trigger_on_release=True)
keyboard.add_hotkey("ctrl+alt+p", launch_patient, trigger_on_release=True)
keyboard.add_hotkey("ctrl+alt+shift+p", launch_nls, trigger_on_release=True)
log("Hotkey listener started (Ctrl+Alt+N / Ctrl+Alt+P / Ctrl+Alt+Shift+P)")
keyboard.wait()
