"""열린 윈도우 목록 확인"""
import win32gui

def list_windows():
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # 제목이 있는 윈도우만
                windows.append(title)
        return True

    win32gui.EnumWindows(callback, None)
    return windows

print("현재 열린 윈도우 목록:")
print("=" * 50)
for title in sorted(list_windows()):
    # NLS 관련 윈도우 강조
    if "nls" in title.lower() or "18d" in title.lower() or "cell" in title.lower():
        print(f">>> {title} <<<")
    else:
        print(f"    {title}")
