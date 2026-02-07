"""
스크린샷에서 버튼 이미지 추출
"""

from PIL import Image
from pathlib import Path

# 스크린샷 경로
SCREENSHOTS_DIR = Path(r"C:\Users\alex\Downloads")
OUTPUT_DIR = Path(__file__).parent.parent / "images"
OUTPUT_DIR.mkdir(exist_ok=True)

# 2560x1440 전체화면 기준 버튼 영역 (x, y, width, height)
# 실제 스크린샷에서 측정한 값
BUTTONS = {
    # 시작 화면 (17 09 31.png) - 640x360 이미지였으므로 4배 스케일
    "btn_start": (152*4, 223*4, 100*4, 25*4),        # START
    "btn_customize": (152*4, 255*4, 100*4, 25*4),   # CUSTOMIZE

    # 환자 카드 화면 (17 09 42.png)
    "btn_new_card": (25, 225, 180, 35),
    "btn_select_card": (258, 225, 180, 35),
    "btn_research": (860, 605, 180, 35),
    "btn_save_to_disk": (290, 340, 180, 35),
    "btn_exit_main": (860, 12, 180, 35),

    # 환자 정보 다이얼로그 (17 11 10.png)
    "btn_ok": (510, 515, 170, 35),
    "btn_cancel": (730, 515, 170, 35),

    # 검사 선택 화면 (17 12 03.png)
    "btn_research_start": (830, 70, 130, 30),

    # 검사 결과 화면 (17 12 29.png) - 560x432 크기
    "btn_exit_scan": (430, 5, 80, 30),
    "btn_pause": (430, 35, 80, 30),
}


def extract_button(screenshot_path: str, button_name: str, region: tuple):
    """스크린샷에서 버튼 영역 추출"""
    try:
        img = Image.open(screenshot_path)
        x, y, w, h = region
        cropped = img.crop((x, y, x + w, y + h))
        output_path = OUTPUT_DIR / f"{button_name}.png"
        cropped.save(output_path)
        print(f"저장됨: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"실패: {button_name} - {e}")
        return None


def main():
    print("버튼 이미지 추출")
    print("=" * 40)

    # 각 스크린샷에서 버튼 추출
    screenshots = {
        "btn_start": "2026-02-02 17 09 31.png",
        "btn_customize": "2026-02-02 17 09 31.png",
        "btn_new_card": "2026-02-02 17 09 42.png",
        "btn_select_card": "2026-02-02 17 09 42.png",
        "btn_research": "2026-02-02 17 09 42.png",
        "btn_exit_main": "2026-02-02 17 09 42.png",
        "btn_ok": "2026-02-02 17 11 10.png",
        "btn_cancel": "2026-02-02 17 11 10.png",
        "btn_research_start": "2026-02-02 17 12 03.png",
        "btn_exit_scan": "2026-02-02 17 12 29.png",
        "btn_pause": "2026-02-02 17 12 29.png",
    }

    for btn_name, region in BUTTONS.items():
        if btn_name in screenshots:
            screenshot = SCREENSHOTS_DIR / screenshots[btn_name]
            if screenshot.exists():
                extract_button(str(screenshot), btn_name, region)
            else:
                print(f"스크린샷 없음: {screenshot}")

    print("\n완료!")
    print(f"이미지 저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
