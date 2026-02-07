"""
NLS 결과 캡처 - 단축키 트리거
F9 키를 누르면 21페이지 결과 캡처 시작
"""

import sys
import time
from pathlib import Path
from datetime import datetime

import pyautogui
import keyboard

# 경로 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from nls_config.nls_config import RESULT_CAPTURE, HOTKEYS

# 안전 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


def capture_results_sequence():
    """
    결과 화면 캡처 시퀀스
    21개 페이지를 순차적으로 캡처
    """
    print("\n" + "=" * 50)
    print("  결과 캡처 시퀀스 시작")
    print("=" * 50)

    # 스크린샷 폴더 생성
    screenshots_dir = BASE_DIR / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    # 1. 캡처 준비 클릭
    print("\n[1] 준비 클릭...")
    pyautogui.click(*RESULT_CAPTURE["btn_before_capture_1"])
    time.sleep(0.5)

    pyautogui.click(*RESULT_CAPTURE["btn_before_capture_2"])
    time.sleep(0.5)

    # 캡처 영역 계산
    x1, y1 = RESULT_CAPTURE["capture_region_start"]
    x2, y2 = RESULT_CAPTURE["capture_region_end"]
    width = x2 - x1
    height = y2 - y1

    print(f"    캡처 영역: ({x1}, {y1}) ~ ({x2}, {y2})")
    print(f"    크기: {width} x {height}")

    results = []
    total_pages = RESULT_CAPTURE["total_pages"]

    # 2. 21번 반복 캡처
    print(f"\n[2] {total_pages}페이지 캡처 시작...")

    for i in range(total_pages):
        # 영역 캡처
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"result_{i+1:02d}_{timestamp}.png"
        filepath = screenshots_dir / filename

        screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        screenshot.save(filepath)

        print(f"    [{i+1:2d}/{total_pages}] {filename}")

        results.append({
            "image_path": str(filepath),
            "timestamp": datetime.now().isoformat(),
            "page": i + 1
        })

        # 마지막 페이지가 아니면 아래 방향키
        if i < total_pages - 1:
            pyautogui.press('down')
            time.sleep(0.3)

    print(f"\n[OK] {len(results)}개 캡처 완료!")
    print(f"    저장 위치: {screenshots_dir}")
    print("=" * 50)

    return results


def main():
    """단축키 리스너 메인"""
    trigger_key = HOTKEYS.get("trigger_capture", "f9")

    print("\n" + "=" * 50)
    print("  NLS 결과 캡처 - 단축키 대기 모드")
    print("=" * 50)
    print(f"\n  [{trigger_key.upper()}] 키를 누르면 캡처 시작")
    print("  [ESC] 키를 누르면 종료")
    print("\n  NLS 리서치가 끝나면 단축키를 누르세요.")
    print("=" * 50)

    # 단축키 등록
    keyboard.add_hotkey(trigger_key, capture_results_sequence)

    # ESC로 종료
    print("\n대기 중... (ESC로 종료)")
    keyboard.wait('esc')

    print("\n종료합니다.")


if __name__ == "__main__":
    main()
