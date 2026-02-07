"""
화면 캡처 모듈
NLS 프로그램 화면을 캡처하여 저장
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pyautogui
import win32gui
import win32ui
import win32con
from PIL import Image


class ScreenCapture:
    """화면 캡처 클래스"""

    def __init__(self, save_dir: str = "./screenshots"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def capture_full_screen(self, filename: Optional[str] = None) -> str:
        """전체 화면 캡처"""
        if not filename:
            filename = self._generate_filename("fullscreen")

        filepath = self.save_dir / filename
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return str(filepath)

    def capture_region(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
        filename: Optional[str] = None
    ) -> str:
        """특정 영역 캡처"""
        if not filename:
            filename = self._generate_filename("region")

        filepath = self.save_dir / filename
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot.save(filepath)
        return str(filepath)

    def capture_window(
        self,
        hwnd: int,
        filename: Optional[str] = None
    ) -> str:
        """특정 윈도우 캡처 (백그라운드 포함)"""
        if not filename:
            filename = self._generate_filename("window")

        filepath = self.save_dir / filename

        # 윈도우 크기 가져오기
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        # 윈도우 DC 가져오기
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # 비트맵 생성
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # 윈도우 내용 복사
        save_dc.BitBlt(
            (0, 0), (width, height),
            mfc_dc, (0, 0),
            win32con.SRCCOPY
        )

        # PIL Image로 변환
        bmp_info = bitmap.GetInfo()
        bmp_str = bitmap.GetBitmapBits(True)
        image = Image.frombuffer(
            'RGB',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_str, 'raw', 'BGRX', 0, 1
        )

        # 저장
        image.save(filepath)

        # 리소스 정리
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return str(filepath)

    def capture_nls_window(
        self,
        window_title: str = "NLS",
        filename: Optional[str] = None
    ) -> Optional[str]:
        """NLS 윈도우 캡처"""
        hwnd = self._find_window(window_title)
        if hwnd:
            return self.capture_window(hwnd, filename)
        return None

    def capture_with_highlight(
        self,
        points: list[Tuple[int, int]],
        filename: Optional[str] = None
    ) -> str:
        """특정 포인트를 강조하여 캡처"""
        from PIL import ImageDraw

        if not filename:
            filename = self._generate_filename("highlight")

        filepath = self.save_dir / filename
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)

        # 각 포인트에 원 그리기
        for x, y in points:
            draw.ellipse(
                [(x - 10, y - 10), (x + 10, y + 10)],
                outline='red',
                width=3
            )

        screenshot.save(filepath)
        return str(filepath)

    def continuous_capture(
        self,
        interval: float = 1.0,
        duration: float = 10.0,
        prefix: str = "continuous"
    ) -> list[str]:
        """연속 캡처"""
        captured_files = []
        start_time = time.time()

        while time.time() - start_time < duration:
            filename = self._generate_filename(prefix)
            filepath = self.capture_full_screen(filename)
            captured_files.append(filepath)
            time.sleep(interval)

        return captured_files

    def _generate_filename(self, prefix: str) -> str:
        """타임스탬프 기반 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{prefix}_{timestamp}.png"

    def _find_window(self, title: str) -> Optional[int]:
        """윈도우 핸들 찾기"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title.lower() in window_title.lower():
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None


class RegionSelector:
    """마우스로 영역 선택하여 캡처"""

    def __init__(self):
        self.start_pos = None
        self.end_pos = None

    def get_region_interactive(self) -> Optional[Tuple[int, int, int, int]]:
        """대화형 영역 선택 (드래그)"""
        import keyboard

        print("영역을 선택하세요. 시작점에서 클릭 후 드래그하고 놓으세요.")
        print("취소하려면 ESC를 누르세요.")

        self.start_pos = None
        self.end_pos = None

        while True:
            if keyboard.is_pressed('escape'):
                print("취소됨")
                return None

            if pyautogui.mouseDown():
                self.start_pos = pyautogui.position()
                while pyautogui.mouseDown():
                    time.sleep(0.01)
                self.end_pos = pyautogui.position()
                break

            time.sleep(0.01)

        if self.start_pos and self.end_pos:
            left = min(self.start_pos[0], self.end_pos[0])
            top = min(self.start_pos[1], self.end_pos[1])
            width = abs(self.end_pos[0] - self.start_pos[0])
            height = abs(self.end_pos[1] - self.start_pos[1])
            return (left, top, width, height)

        return None
