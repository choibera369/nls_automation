"""
NLS 버튼 이미지 크롭 스크립트
Windows에서 실행: python crop_buttons.py
"""

from PIL import Image
from pathlib import Path

# 경로 설정
DOWNLOADS = Path(r"C:\Users\alex\Downloads")
OUTPUT = Path(__file__).parent / "images"
OUTPUT.mkdir(exist_ok=True)

def crop_button(screenshot: str, name: str, bbox: tuple):
    """버튼 크롭 및 저장"""
    path = DOWNLOADS / screenshot
    if not path.exists():
        print(f"[!] 파일 없음: {path}")
        return

    img = Image.open(path)
    print(f"[*] {screenshot}: {img.size}")

    cropped = img.crop(bbox)
    output = OUTPUT / f"{name}.png"
    cropped.save(output)
    print(f"    -> {name}.png ({cropped.size[0]}x{cropped.size[1]})")


def main():
    print("=" * 50)
    print("  NLS 버튼 이미지 크롭")
    print("=" * 50)

    # 2560x1440 해상도 기준 좌표 (left, top, right, bottom)

    # 1. 시작 화면 - START, CUSTOMIZE, EXIT
    # 버튼들이 화면 왼쪽 중앙에 위치
    crop_button(
        "2026-02-02 17 09 31.png",
        "btn_start",
        (540, 870, 800, 940)  # START 버튼
    )
    crop_button(
        "2026-02-02 17 09 31.png",
        "btn_customize",
        (540, 1000, 800, 1070)  # CUSTOMIZE 버튼
    )

    # 2. 환자 카드 화면 - NEW CARD, SELECT CARD, RESEARCH 등
    crop_button(
        "2026-02-02 17 09 42.png",
        "btn_new_card",
        (22, 420, 230, 465)  # NEW CARD
    )
    crop_button(
        "2026-02-02 17 09 42.png",
        "btn_select_card",
        (250, 420, 470, 465)  # SELECT CARD
    )
    crop_button(
        "2026-02-02 17 09 42.png",
        "btn_save_to_disk",
        (280, 630, 505, 675)  # SAVE TO DISK
    )
    crop_button(
        "2026-02-02 17 09 42.png",
        "btn_view_analysis",
        (520, 630, 745, 675)  # VIEW ANALYSIS
    )
    crop_button(
        "2026-02-02 17 09 42.png",
        "btn_exit_main",
        (1745, 10, 1920, 50)  # EXIT (우측 상단)
    )
    crop_button(
        "2026-02-02 17 09 42.png",
        "btn_research",
        (1720, 1100, 1920, 1145)  # RESEARCH (우측 하단)
    )

    # 3. 환자 정보 다이얼로그 - OK, CANCEL
    crop_button(
        "2026-02-02 17 11 10.png",
        "btn_ok",
        (980, 1040, 1180, 1085)  # OK
    )
    crop_button(
        "2026-02-02 17 11 10.png",
        "btn_cancel",
        (1220, 1040, 1420, 1085)  # CANCEL
    )

    # 4. 검사 결과 화면 - EXIT, PAUSE
    crop_button(
        "2026-02-02 17 12 29.png",
        "btn_exit_scan",
        (1680, 25, 1840, 65)  # EXIT
    )
    crop_button(
        "2026-02-02 17 12 29.png",
        "btn_pause",
        (1680, 70, 1840, 110)  # PAUSE
    )

    print("\n" + "=" * 50)
    print(f"완료! 이미지 저장 위치: {OUTPUT}")
    print("=" * 50)

    # 결과 확인
    images = list(OUTPUT.glob("*.png"))
    print(f"\n생성된 이미지 ({len(images)}개):")
    for img_path in sorted(images):
        img = Image.open(img_path)
        print(f"  {img_path.name}: {img.size[0]}x{img.size[1]}")


def interactive_crop():
    """대화형 크롭 모드 - 좌표 직접 입력"""
    print("\n=== 대화형 크롭 모드 ===")
    print("스크린샷에서 버튼 좌표를 직접 입력합니다.")
    print("좌표 확인 방법: 그림판에서 이미지 열고 마우스 위치 확인\n")

    # 스크린샷 목록
    screenshots = sorted(DOWNLOADS.glob("2026-02-02*.png"))
    print("스크린샷 목록:")
    for i, s in enumerate(screenshots):
        img = Image.open(s)
        print(f"  {i+1}. {s.name} ({img.size[0]}x{img.size[1]})")

    while True:
        print("\n옵션: [번호] 스크린샷 선택, [q] 종료")
        choice = input("> ").strip()

        if choice.lower() == 'q':
            break

        try:
            idx = int(choice) - 1
            screenshot = screenshots[idx]
        except (ValueError, IndexError):
            print("잘못된 선택")
            continue

        name = input("버튼 이름 (예: btn_start): ").strip()
        coords = input("좌표 (left,top,right,bottom): ").strip()

        try:
            left, top, right, bottom = map(int, coords.split(","))
            crop_button(screenshot.name, name, (left, top, right, bottom))
        except ValueError:
            print("좌표 형식 오류. 예: 540,870,800,940")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        interactive_crop()
    else:
        main()
        print("\n팁: 좌표가 안 맞으면 'python crop_buttons.py -i'로 대화형 모드 실행")
