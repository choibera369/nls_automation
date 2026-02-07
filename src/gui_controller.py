"""
NLS 프로그램 GUI 제어 모듈
pyautogui를 사용하여 Windows GUI 자동화
"""

import time
import pyautogui
import win32gui
import win32con
from typing import Optional, Tuple


class NLSController:
    """NLS 프로그램 GUI 제어 클래스"""

    def __init__(self, window_title: str = "NLS"):
        self.window_title = window_title
        self.hwnd: Optional[int] = None
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    def find_window(self) -> bool:
        """NLS 윈도우 찾기"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.window_title.lower() in title.lower():
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)

        if windows:
            self.hwnd = windows[0]
            return True
        return False

    def activate_window(self) -> bool:
        """NLS 윈도우 활성화"""
        if not self.hwnd:
            if not self.find_window():
                return False

        try:
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"윈도우 활성화 실패: {e}")
            return False

    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """윈도우 위치와 크기 반환 (left, top, right, bottom)"""
        if not self.hwnd:
            if not self.find_window():
                return None
        return win32gui.GetWindowRect(self.hwnd)

    def click_at(self, x: int, y: int, clicks: int = 1):
        """지정 좌표 클릭"""
        pyautogui.click(x, y, clicks=clicks)

    def click_relative(self, x_offset: int, y_offset: int, clicks: int = 1):
        """윈도우 기준 상대 좌표 클릭"""
        rect = self.get_window_rect()
        if rect:
            abs_x = rect[0] + x_offset
            abs_y = rect[1] + y_offset
            self.click_at(abs_x, abs_y, clicks)

    def double_click(self, x: int, y: int):
        """더블 클릭"""
        pyautogui.doubleClick(x, y)

    def right_click(self, x: int, y: int):
        """우클릭"""
        pyautogui.rightClick(x, y)

    def type_text(self, text: str, interval: float = 0.05):
        """텍스트 입력"""
        pyautogui.typewrite(text, interval=interval)

    def press_key(self, key: str):
        """키 입력"""
        pyautogui.press(key)

    def hotkey(self, *keys):
        """단축키 입력"""
        pyautogui.hotkey(*keys)

    def move_to(self, x: int, y: int, duration: float = 0.3):
        """마우스 이동"""
        pyautogui.moveTo(x, y, duration=duration)

    def drag_to(self, x: int, y: int, duration: float = 0.5):
        """드래그"""
        pyautogui.dragTo(x, y, duration=duration)

    def scroll(self, clicks: int):
        """스크롤 (양수: 위로, 음수: 아래로)"""
        pyautogui.scroll(clicks)

    def wait_for_image(
        self,
        image_path: str,
        timeout: float = 10.0,
        confidence: float = 0.9
    ) -> Optional[Tuple[int, int]]:
        """이미지가 화면에 나타날 때까지 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateCenterOnScreen(
                    image_path,
                    confidence=confidence
                )
                if location:
                    return location
            except pyautogui.ImageNotFoundException:
                pass
            time.sleep(0.5)
        return None

    def click_image(
        self,
        image_path: str,
        confidence: float = 0.9,
        timeout: float = 10.0
    ) -> bool:
        """이미지 찾아서 클릭"""
        location = self.wait_for_image(image_path, timeout, confidence)
        if location:
            self.click_at(location[0], location[1])
            return True
        return False


# 사전 정의된 NLS 작업들
class NLSActions:
    """NLS 프로그램 주요 작업 모음"""

    def __init__(self, controller: NLSController):
        self.ctrl = controller

    def start_scan(self):
        """검사 시작"""
        self.ctrl.activate_window()
        # 검사 시작 버튼 위치 (실제 좌표로 수정 필요)
        self.ctrl.click_relative(100, 200)

    def stop_scan(self):
        """검사 중지"""
        self.ctrl.activate_window()
        self.ctrl.press_key('escape')

    def next_page(self):
        """다음 페이지"""
        self.ctrl.activate_window()
        self.ctrl.press_key('right')

    def prev_page(self):
        """이전 페이지"""
        self.ctrl.activate_window()
        self.ctrl.press_key('left')

    def save_result(self):
        """결과 저장"""
        self.ctrl.activate_window()
        self.ctrl.hotkey('ctrl', 's')

    def open_menu(self, menu_name: str):
        """메뉴 열기"""
        self.ctrl.activate_window()
        self.ctrl.hotkey('alt')
        time.sleep(0.2)
        self.ctrl.type_text(menu_name[0])
