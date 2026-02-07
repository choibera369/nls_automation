"""
UI 요소 이미지 캡처 도구
NLS 프로그램의 버튼, 아이콘 등을 캡처하여 참조 이미지로 저장
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

import pyautogui
import keyboard
from PIL import Image, ImageDraw, ImageFont

# 이미지 저장 경로
IMAGES_DIR = Path(__file__).parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)


class ImageCaptureTool:
    """UI 요소 이미지 캡처 도구"""

    def __init__(self):
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False

    def capture_region_interactive(self, name: str = None) -> str:
        """
        마우스 드래그로 영역 선택하여 캡처

        사용법:
        1. 실행 후 캡처할 영역의 좌상단에서 마우스 왼쪽 버튼 누르기
        2. 우하단까지 드래그
        3. 마우스 버튼 놓기
        """
        print("\n=== 영역 캡처 모드 ===")
        print("1. 캡처할 영역의 좌상단에서 마우스 왼쪽 버튼을 누르세요")
        print("2. 우하단까지 드래그하세요")
        print("3. 마우스 버튼을 놓으세요")
        print("취소: ESC 키")
        print()

        self.selection_start = None
        self.selection_end = None

        # 마우스 클릭 대기
        while True:
            if keyboard.is_pressed('escape'):
                print("취소됨")
                return None

            # 마우스 버튼 상태 확인 (pyautogui는 직접 지원 안함)
            # 간단한 방법: 위치 변화 감지
            import ctypes
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:  # 왼쪽 마우스 버튼
                self.selection_start = pyautogui.position()
                print(f"시작점: {self.selection_start}")

                # 버튼 놓을 때까지 대기
                while ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                    time.sleep(0.01)

                self.selection_end = pyautogui.position()
                print(f"끝점: {self.selection_end}")
                break

            time.sleep(0.01)

        # 영역 계산
        left = min(self.selection_start[0], self.selection_end[0])
        top = min(self.selection_start[1], self.selection_end[1])
        width = abs(self.selection_end[0] - self.selection_start[0])
        height = abs(self.selection_end[1] - self.selection_start[1])

        if width < 5 or height < 5:
            print("영역이 너무 작습니다. 다시 시도하세요.")
            return None

        # 캡처
        screenshot = pyautogui.screenshot(region=(left, top, width, height))

        # 파일명 생성
        if not name:
            name = input("이미지 이름 입력 (예: btn_start): ").strip()
            if not name:
                name = f"capture_{datetime.now().strftime('%H%M%S')}"

        filename = f"{name}.png"
        filepath = IMAGES_DIR / filename
        screenshot.save(filepath)

        print(f"저장됨: {filepath}")
        print(f"크기: {width} x {height}")

        return str(filepath)

    def capture_at_cursor(self, size: int = 50, name: str = None) -> str:
        """
        현재 커서 위치 중심으로 정사각형 영역 캡처

        사용법:
        1. 캡처할 버튼/아이콘 위에 마우스 올리기
        2. Space 키 누르기
        """
        print(f"\n=== 커서 위치 캡처 모드 ({size}x{size}) ===")
        print("캡처할 버튼/아이콘 위에 마우스를 올리고 SPACE를 누르세요")
        print("취소: ESC 키")
        print()

        while True:
            if keyboard.is_pressed('escape'):
                print("취소됨")
                return None

            if keyboard.is_pressed('space'):
                pos = pyautogui.position()
                left = pos[0] - size // 2
                top = pos[1] - size // 2

                screenshot = pyautogui.screenshot(region=(left, top, size, size))

                if not name:
                    name = input("이미지 이름 입력: ").strip()
                    if not name:
                        name = f"icon_{datetime.now().strftime('%H%M%S')}"

                filename = f"{name}.png"
                filepath = IMAGES_DIR / filename
                screenshot.save(filepath)

                print(f"저장됨: {filepath}")
                return str(filepath)

            time.sleep(0.05)

    def capture_multiple(self):
        """여러 UI 요소 연속 캡처"""
        print("\n=== 연속 캡처 모드 ===")
        print("여러 UI 요소를 연속으로 캡처합니다.")
        print()

        captured = []
        while True:
            name = input("\n이미지 이름 (종료: q): ").strip()
            if name.lower() == 'q':
                break

            mode = input("캡처 모드 (1: 영역 드래그, 2: 커서 위치): ").strip()

            if mode == '1':
                path = self.capture_region_interactive(name)
            else:
                size = input("캡처 크기 (기본 50): ").strip()
                size = int(size) if size else 50
                path = self.capture_at_cursor(size, name)

            if path:
                captured.append(path)

        print(f"\n총 {len(captured)}개 이미지 캡처 완료")
        for p in captured:
            print(f"  - {p}")

        return captured

    def show_mouse_position(self):
        """실시간 마우스 좌표 표시"""
        print("\n=== 마우스 좌표 표시 모드 ===")
        print("마우스를 움직이면 좌표가 표시됩니다.")
        print("종료: ESC 키")
        print()

        try:
            while True:
                if keyboard.is_pressed('escape'):
                    break

                x, y = pyautogui.position()
                # 같은 줄에 업데이트
                print(f"\r좌표: X={x:4d}, Y={y:4d}    ", end='', flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

        print("\n종료")

    def list_saved_images(self):
        """저장된 이미지 목록"""
        print(f"\n=== 저장된 이미지 ({IMAGES_DIR}) ===")

        images = list(IMAGES_DIR.glob("*.png"))
        if not images:
            print("저장된 이미지가 없습니다.")
            return

        for img in sorted(images):
            size = Image.open(img).size
            print(f"  {img.name:<30} {size[0]:>4}x{size[1]:<4}")

    def preview_image(self, name: str):
        """이미지 미리보기"""
        filepath = IMAGES_DIR / f"{name}.png"
        if not filepath.exists():
            filepath = IMAGES_DIR / name
            if not filepath.exists():
                print(f"이미지를 찾을 수 없습니다: {name}")
                return

        img = Image.open(filepath)
        img.show()


def main():
    """메인 진입점"""
    tool = ImageCaptureTool()

    while True:
        print("\n=== NLS 이미지 캡처 도구 ===")
        print("1. 영역 드래그 캡처")
        print("2. 커서 위치 캡처")
        print("3. 연속 캡처")
        print("4. 마우스 좌표 확인")
        print("5. 저장된 이미지 목록")
        print("6. 종료")
        print()

        choice = input("선택: ").strip()

        if choice == '1':
            tool.capture_region_interactive()
        elif choice == '2':
            size = input("캡처 크기 (기본 50): ").strip()
            size = int(size) if size else 50
            tool.capture_at_cursor(size)
        elif choice == '3':
            tool.capture_multiple()
        elif choice == '4':
            tool.show_mouse_position()
        elif choice == '5':
            tool.list_saved_images()
        elif choice == '6':
            print("종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
