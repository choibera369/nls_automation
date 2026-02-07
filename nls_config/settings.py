"""
NLS 자동화 설정
좌표, 타이밍, UI 요소 위치 등을 정의
"""

# NLS 프로그램 UI 좌표 (실제 프로그램에 맞게 수정 필요)
# 모든 좌표는 윈도우 기준 상대 좌표

UI_ELEMENTS = {
    # 메인 메뉴
    "menu_file": (50, 30),
    "menu_scan": (120, 30),
    "menu_analysis": (200, 30),
    "menu_report": (280, 30),
    "menu_help": (350, 30),

    # 스캔 컨트롤
    "btn_start_scan": (100, 100),
    "btn_stop_scan": (200, 100),
    "btn_pause_scan": (300, 100),

    # 네비게이션
    "btn_prev_page": (50, 700),
    "btn_next_page": (750, 700),
    "btn_home": (400, 700),

    # 결과 영역
    "result_area": (100, 150, 700, 600),  # (x, y, width, height)
    "indicator_panel": (720, 150, 250, 400),

    # 환자 정보
    "patient_name": (150, 50),
    "patient_id": (350, 50),
}

# 색상 코드 (NLS 결과 해석용)
COLOR_CODES = {
    "yellow": "정상 범위",
    "orange": "주의 필요",
    "red": "이상 감지",
    "blue": "저하 상태",
    "green": "양호",
    "black": "심각한 이상",
}

# 스캔 타입별 페이지 수
SCAN_PAGES = {
    "full_body": 12,
    "head": 4,
    "chest": 3,
    "abdomen": 4,
    "spine": 5,
    "limbs": 6,
}

# 타이밍 설정 (초)
TIMING = {
    "page_load_delay": 2.0,
    "scan_stabilize": 1.5,
    "click_interval": 0.5,
    "animation_wait": 0.3,
}

# AI 분석 프롬프트
ANALYSIS_PROMPTS = {
    "general": """
이 NLS 검사 화면을 분석해주세요.
검사 부위, 이상 신호, 전반적인 상태를 평가해주세요.
""",

    "detailed": """
이 NLS 검사 화면을 상세히 분석해주세요.

1. 검사 부위 식별
2. 색상별 신호 분석 (노란색=정상, 주황색=주의, 빨간색=이상)
3. 수치/지표 해석
4. 이상 패턴 감지
5. 권장 조치사항

JSON 형식으로 구조화된 결과를 제공해주세요.
""",

    "comparison": """
두 검사 결과를 비교 분석해주세요.
변화된 부분, 개선/악화 영역, 추세를 파악해주세요.
""",

    "organ_specific": """
이 장기 검사 결과를 분석해주세요.
해당 장기의 상태, 기능 지표, 주의사항을 알려주세요.
""",
}

# 장기별 검사 영역 (ROI: Region of Interest)
ORGAN_REGIONS = {
    "brain": {"page": 1, "region": (150, 200, 400, 350)},
    "heart": {"page": 3, "region": (200, 250, 350, 300)},
    "liver": {"page": 5, "region": (180, 220, 380, 320)},
    "kidney": {"page": 6, "region": (160, 280, 400, 340)},
    "stomach": {"page": 7, "region": (200, 240, 360, 300)},
    "intestine": {"page": 8, "region": (150, 260, 420, 360)},
}

# 단축키 매핑
HOTKEYS = {
    "start_scan": ["ctrl", "s"],
    "stop_scan": ["escape"],
    "next_page": ["right"],
    "prev_page": ["left"],
    "save": ["ctrl", "shift", "s"],
    "print": ["ctrl", "p"],
    "zoom_in": ["ctrl", "+"],
    "zoom_out": ["ctrl", "-"],
}
