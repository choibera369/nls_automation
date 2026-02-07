"""
스크린샷에서 버튼 이미지 크롭
Windows에서 실행: python crop_buttons.py
"""

from PIL import Image
from pathlib import Path

# 경로 설정
DOWNLOADS = Path(r"C:\Users\alex\Downloads")
OUTPUT = Path(__file__).parent.parent / "images"
OUTPUT.mkdir(exist_ok=True)

def crop_and_save(screenshot_name: str, button_name: str, bbox: tuple):
    """
    스크린샷에서 버튼 영역 크롭

    Args:
        screenshot_name: 스크린샷 파일명
        button_name: 저장할 버튼 이름
        bbox: (left, top, right, bottom) 좌표
    """
    screenshot_path = DOWNLOADS / screenshot_name
    if not screenshot_path.exists():
        print(f"[!] 스크린샷 없음: {screenshot_path}")
        return

    img = Image.open(screenshot_path)
    cropped = img.crop(bbox)
    output_path = OUTPUT / f"{button_name}.png"
    cropped.save(output_path)
    print(f"[+] 저장: {output_path} ({cropped.size[0]}x{cropped.size[1]})")


def main():
    print("=" * 50)
    print("  NLS 버튼 이미지 크롭")
    print("=" * 50)
    print(f"\n스크린샷 폴더: {DOWNLOADS}")
    print(f"출력 폴더: {OUTPUT}\n")

    # ============================================================
    # 버튼 좌표 정의 (직접 측정 필요!)
    # bbox = (left, top, right, bottom)
    # ============================================================

    # 1. 시작 화면 (2026-02-02 17 09 31.png)
    # START, CUSTOMIZE, EXIT 버튼
    # 이미지 크기 확인 후 수동 조정 필요

    # 2. 환자 카드 화면 (2026-02-02 17 09 42.png)
    # NEW CARD, SELECT CARD, RESEARCH 버튼

    # 3. 환자 정보 다이얼로그 (2026-02-02 17 11 10.png)
    # OK, CANCEL 버튼

    # 4. 검사 결과 화면 (2026-02-02 17 12 29.png)
    # EXIT, PAUSE 버튼

    print("=" * 50)
    print("  수동 버튼 크롭 모드")
    print("=" * 50)
    print("""
사용법:
1. 스크린샷을 그림판이나 이미지 뷰어로 열기
2. 버튼 영역의 좌표 확인 (left, top, right, bottom)
3. 아래 함수 호출로 크롭

예시:
  crop_and_save("2026-02-02 17 09 31.png", "btn_start", (550, 870, 750, 930))

또는 대화형 모드로 입력:
""")

    while True:
        print("\n옵션:")
        print("  1. 버튼 크롭 (좌표 입력)")
        print("  2. 스크린샷 목록 보기")
        print("  3. 종료")

        choice = input("\n선택: ").strip()

        if choice == "1":
            screenshot = input("스크린샷 파일명: ").strip()
            button = input("버튼 이름 (예: btn_start): ").strip()
            coords = input("좌표 (left,top,right,bottom): ").strip()

            try:
                left, top, right, bottom = map(int, coords.split(","))
                crop_and_save(screenshot, button, (left, top, right, bottom))
            except ValueError:
                print("[!] 좌표 형식 오류. 예: 550,870,750,930")

        elif choice == "2":
            screenshots = list(DOWNLOADS.glob("2026-02-02*.png"))
            print(f"\n스크린샷 {len(screenshots)}개:")
            for s in sorted(screenshots):
                img = Image.open(s)
                print(f"  {s.name} - {img.size[0]}x{img.size[1]}")

        elif choice == "3":
            break


if __name__ == "__main__":
    main()
