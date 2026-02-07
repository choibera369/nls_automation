"""
마우스 좌표 실시간 확인
NLS 프로그램 위에서 버튼 위치 확인용
"""
import pyautogui
import time

print("=" * 50)
print("  마우스 좌표 확인 (Ctrl+C로 종료)")
print("=" * 50)
print("\nNLS 프로그램 버튼 위에 마우스를 올리고 좌표를 확인하세요.\n")

try:
    while True:
        x, y = pyautogui.position()
        print(f"\r  X: {x:4d}  Y: {y:4d}    ", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n종료")
