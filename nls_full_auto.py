# -*- coding: utf-8 -*-
"""
NLS 18D CELL Full Automation Script
2K Resolution (2560x1440)

핫키:
- F9: 21페이지 결과 캡쳐 시작
- SHIFT+ALT+F9: Gemini 분석 시작
- ESC: 프로그램 종료
"""

import os
import sys
import time
import json
from datetime import datetime, date
from pathlib import Path

# Windows cp949 콘솔에서 스페인어 특수문자(í,ñ,á 등) 깨짐 방지
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import pyautogui
import win32gui
import win32con
import pyperclip
import keyboard
from PIL import Image
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from nls_config.nls_config import (
    START_SCREEN,
    CLEANUP_SEQUENCE,
    PATIENT_DIALOG,
    RESULT_CAPTURE,
    HOTKEYS,
    BLOOD_TYPE_MAP,
    RH_FACTOR_MAP,
    TIMING,
    NLS_WINDOW,
    GEMINI,
)

# pyautogui 안전 설정
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


def _convert_patient_row(p):
    """Supabase 환자 row를 NLS 형식 dict로 변환"""
    # nombre → last_name, first_name 분리
    # Supabase에 "이름 성" 형태로 저장됨
    parts = (p.get("nombre") or "").strip().split()
    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    # fecha_nacimiento → year, month, day
    birth = {"year": 1990, "month": 1, "day": 1}
    fecha = p.get("fecha_nacimiento")
    if fecha:
        d = date.fromisoformat(fecha)
        birth = {"year": d.year, "month": d.month, "day": d.day}

    # sexo: "masculino" → "MALE", "femenino" → "FEMALE"
    sexo = (p.get("sexo") or "").lower()
    gender = "MALE" if sexo == "masculino" else "FEMALE"

    # tipo_sangre: null → "?"
    blood_type = p.get("tipo_sangre") or "?"

    # factor_rh: null → "?"
    rh_factor = p.get("factor_rh") or "?"

    return {
        "patient_id": p.get("id"),
        "last_name": last_name,
        "first_name": first_name,
        "birth_date": birth,
        "gender": gender,
        "blood_type": blood_type,
        "rh_factor": rh_factor,
    }


def _print_patient_info(patient_data):
    """선택된 환자 정보 출력"""
    print(f"  → Last Name: {patient_data['last_name']}")
    print(f"  → First Name: {patient_data['first_name']}")
    print(f"  → Birth Date: {patient_data['birth_date']}")
    print(f"  → Gender: {patient_data['gender']}")
    print(f"  → Blood Type: {patient_data['blood_type']}")
    print(f"  → RH Factor: {patient_data['rh_factor']}")


def _select_from_list(patients):
    """환자 목록에서 선택"""
    print("\n" + "=" * 65)
    print("  환자 목록")
    print("=" * 65)
    for i, p in enumerate(patients, 1):
        nombre = p.get("nombre") or "(이름없음)"
        telefono = p.get("telefono") or "N/A"
        fecha = p.get("fecha_nacimiento") or "N/A"
        sexo = p.get("sexo") or "N/A"
        created = (p.get("created_at") or "")[:16].replace("T", " ")
        print(f"  {i}. {nombre:<20} Tel:{telefono:<12} 생년:{fecha}  성별:{sexo}  등록:{created}")
    print("-" * 65)
    print("  0. 취소")
    print("-" * 65)

    while True:
        choice = input("\nSelect patient (0=cancel): ").strip()
        if choice == "0":
            print("[SUPABASE] Cancelled")
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(patients):
            break
        print(f"  Enter 1~{len(patients)} or 0")

    p = patients[int(choice) - 1]
    print(f"\n[SUPABASE] 선택된 환자: {p['nombre']}")

    patient_data = _convert_patient_row(p)
    _print_patient_info(patient_data)
    return patient_data


def fetch_latest_patient():
    """Supabase에서 전화번호 검색 또는 최근 환자 목록에서 선택"""
    load_dotenv(PROJECT_ROOT / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("[SUPABASE] SUPABASE_URL 또는 SUPABASE_ANON_KEY가 .env에 없습니다.")
        return None

    try:
        from supabase import create_client
        sb = create_client(url, key)

        select_fields = "id, nombre, telefono, fecha_nacimiento, sexo, tipo_sangre, factor_rh, created_at"

        # 검색 방법 선택
        print("\n" + "=" * 55)
        print("  환자 검색")
        print("=" * 55)
        print("  전화번호를 입력하거나 Enter를 누르면 최근 목록을 표시합니다.")
        print("-" * 55)
        phone = input("\n  Telefono (Enter=최근목록): ").strip()

        if phone:
            # 전화번호로 검색 (부분 매칭)
            res = (
                sb.table("patients")
                .select(select_fields)
                .ilike("telefono", f"%{phone}%")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )

            if not res.data:
                print(f"[SUPABASE] '{phone}' 번호로 등록된 환자가 없습니다.")
                print("  최근 환자 목록으로 전환합니다...\n")
                # 전화번호 검색 실패 시 최근 목록으로 폴백
                res = (
                    sb.table("patients")
                    .select(select_fields)
                    .order("created_at", desc=True)
                    .limit(10)
                    .execute()
                )
                if not res.data:
                    print("[SUPABASE] 등록된 환자가 없습니다.")
                    return None
            else:
                print(f"[SUPABASE] '{phone}' 검색 결과: {len(res.data)}명")
        else:
            # 최근 10명 표시
            res = (
                sb.table("patients")
                .select(select_fields)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )

            if not res.data:
                print("[SUPABASE] 등록된 환자가 없습니다.")
                return None

        return _select_from_list(res.data)

    except Exception as e:
        print(f"[SUPABASE] 오류: {e}")
        return None


def save_result_to_supabase(patient_id, analysis_text, image_count):
    """분석 결과를 Supabase nls_results 테이블에 저장"""
    load_dotenv(PROJECT_ROOT / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("[SUPABASE] 저장 실패: 환경변수 없음")
        return False

    try:
        from supabase import create_client
        sb = create_client(url, key)

        sb.table("nls_results").insert({
            "patient_id": patient_id,
            "analysis_text": analysis_text,
            "image_count": image_count,
        }).execute()

        print(f"[SUPABASE] 분석 결과 저장 완료 (patient_id: {patient_id})")
        return True

    except Exception as e:
        print(f"[SUPABASE] 저장 오류: {e}")
        return False


def save_selected_patient(patient_id):
    """선택된 환자 ID를 selected_patient.json에 저장 (patient_app과 공유)"""
    try:
        selected_file = PROJECT_ROOT / "selected_patient.json"
        selected_file.write_text(
            json.dumps({"patient_id": patient_id}), encoding="utf-8"
        )
        print(f"[SYNC] selected_patient.json 저장 완료")
    except Exception as e:
        print(f"[SYNC] 저장 실패: {e}")


class NLSFullAutomation:
    """NLS 18D CELL 전체 자동화 클래스"""

    def __init__(self):
        self.screenshots_dir = PROJECT_ROOT / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = PROJECT_ROOT / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.captured_images = []
        self.running = True
        self.current_patient_id = None


    def activate_nls_window(self):
        """NLS 프로그램 창을 찾아서 맨 앞으로 가져오기 (3번 재시도)"""
        print("[WINDOW] NLS 창 찾는 중...")

        nls_hwnd = None
        best_score = 0

        def callback(hwnd, param):
            nonlocal nls_hwnd, best_score
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                title_lower = title.lower()

                # 자기 자신(콘솔/자동화 창) 및 브라우저 제외
                skip_keywords = (
                    "nls_automation", "cmd.exe", "python",
                    "chrome", "firefox", "edge", "opera", "brave",
                    "explorer",
                )
                if any(kw in title_lower for kw in skip_keywords):
                    return True

                # 우선순위: the18dnls(정확한 프로그램) > 18d
                score = 0
                if "the18dnls" in title_lower:
                    score = 3
                elif "18d" in title_lower:
                    score = 2

                if score > best_score:
                    best_score = score
                    nls_hwnd = hwnd
            return True

        win32gui.EnumWindows(callback, None)
        
        if nls_hwnd:
            title = win32gui.GetWindowText(nls_hwnd)
            print(f"[WINDOW] 찾음: {title}")
            
            # 3번 재시도
            for attempt in range(3):
                try:
                    # 최소화 상태면 복원
                    if win32gui.IsIconic(nls_hwnd):
                        win32gui.ShowWindow(nls_hwnd, win32con.SW_RESTORE)
                        time.sleep(0.3)
                    
                    # Alt 키 누르고 있는 동안 SetForegroundWindow 호출
                    import ctypes
                    ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt 누름
                    time.sleep(0.05)
                    win32gui.SetForegroundWindow(nls_hwnd)
                    time.sleep(0.05)
                    ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt 뗌
                    
                    time.sleep(0.3)
                    
                    # 활성화 확인
                    if win32gui.GetForegroundWindow() == nls_hwnd:
                        print(f"[WINDOW] NLS 창 활성화 완료 (시도 {attempt + 1})")
                        time.sleep(0.5)
                        return True
                    else:
                        print(f"[WINDOW] 시도 {attempt + 1} 실패, 재시도...")
                        time.sleep(0.3)
                        
                except Exception as e:
                    print(f"[WINDOW] 시도 {attempt + 1} 에러: {e}")
                    time.sleep(0.3)
            
            # 마지막 시도: 클릭으로 활성화
            print("[WINDOW] 클릭으로 활성화 시도...")
            rect = win32gui.GetWindowRect(nls_hwnd)
            x = rect[0] + 100
            y = rect[1] + 50
            pyautogui.click(x, y)
            time.sleep(0.5)
            return True
        else:
            print("[WINDOW] NLS 창을 찾을 수 없습니다!")
            return False

    def click(self, coords, delay=None):
        """좌표 클릭"""
        if delay is None:
            delay = TIMING["click_delay"]
        pyautogui.click(coords[0], coords[1])
        time.sleep(delay)

    def type_text(self, text):
        """텍스트 입력 (클립보드 사용)"""
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)

    def type_ascii(self, text):
        """ASCII 텍스트 입력"""
        pyautogui.typewrite(text, interval=TIMING["typing_interval"])

    def select_dropdown(self, coords, down_count):
        """드롭다운 선택 (키보드 방향키 사용)"""
        self.click(coords, delay=TIMING["dropdown_delay"])
        time.sleep(0.5)
        for _ in range(down_count):
            pyautogui.press("down")
            time.sleep(0.3)
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.5)

    def select_gender(self, gender):
        """성별 선택 (마우스 클릭)"""
        # 드롭다운 열기
        coords = PATIENT_DIALOG["dropdown_gender"]
        self.click(coords, delay=TIMING["dropdown_delay"])
        time.sleep(0.5)
        
        if gender.upper() == "MALE":
            # MALE 클릭 (1626, 582)
            pyautogui.click(1626, 582)
        else:
            # FEMALE 클릭 (1626, 611)
            pyautogui.click(1626, 611)
        
        time.sleep(0.5)
    def select_blood_type(self, blood_type):
        """혈액형 선택 (스페이스바 2번으로 O 안착 후 down으로 이동)"""
        coords = PATIENT_DIALOG["dropdown_blood_type"]
        self.click(coords, delay=TIMING["dropdown_delay"])
        time.sleep(0.3)
        
        # 스페이스바 2번 - O에 안착
        for _ in range(2):
            pyautogui.press("space")
            time.sleep(0.4)
        
        time.sleep(0.3)
        
        # O=0, A=1, B=2, AB=3, ?=4
        blood_map = {"O": 0, "A": 1, "B": 2, "AB": 3, "?": 4}
        down_count = blood_map.get(blood_type.upper(), 0)
        
        for _ in range(down_count):
            pyautogui.press("down")
            time.sleep(0.1)
        
        pyautogui.press("enter")
        time.sleep(0.2)


    def input_birth_date(self, year, month, day):
        """생년월일 입력 (년 -> 오른쪽 -> 월 -> 오른쪽 -> 일)"""
        coords = PATIENT_DIALOG["input_birth_date"]
        self.click(coords)
        time.sleep(0.5)
        
        # 년도 입력
        pyautogui.typewrite(str(year), interval=0.05)
        time.sleep(0.2)
        pyautogui.press("right")
        time.sleep(0.2)
        
        # 월 입력
        pyautogui.typewrite(str(month).zfill(2), interval=0.05)
        time.sleep(0.2)
        pyautogui.press("right")
        time.sleep(0.2)
        
        # 일 입력
        pyautogui.typewrite(str(day).zfill(2), interval=0.05)
        time.sleep(0.2)

    def cleanup_existing_user(self):
        """기존 테스트 사용자 삭제 (6번 클릭 시퀀스)"""
        print("[CLEANUP] 기존 사용자 삭제 시작...")
        for i, coords in enumerate(CLEANUP_SEQUENCE, 1):
            print(f"  클릭 {i}/6: {coords}")
            self.click(coords, delay=0.5)
        print("[CLEANUP] 완료")

    def fill_patient_info(self, patient_data):
        """환자 정보 입력"""
        print("[PATIENT] 환자 정보 입력 시작...")
        
        # 1. Last Name (3번 클릭으로 안정화)
        print("  - Last Name 입력")
        for _ in range(3):
            pyautogui.click(PATIENT_DIALOG["input_last_name"][0], PATIENT_DIALOG["input_last_name"][1])
            time.sleep(0.2)
        time.sleep(0.3)
        self.type_text(patient_data.get("last_name", "TEST"))
        time.sleep(0.3)
        
        # 2. First Name (Tab으로 이동)
        print("  - First Name 입력")
        pyautogui.press("tab")
        time.sleep(0.3)
        self.type_text(patient_data.get("first_name", "USER"))
        time.sleep(0.3)
        
        # 3. Birth Date
        print("  - Birth Date 입력")
        birth = patient_data.get("birth_date", {"year": 1990, "month": 1, "day": 1})
        self.input_birth_date(birth["year"], birth["month"], birth["day"])
        
        # 4. Blood Type
        print("  - Blood Type 선택")
        blood_type = patient_data.get("blood_type", "A")
        self.select_blood_type(blood_type)
        time.sleep(1.0)  # 드롭다운 완료 대기
        
        # 5. RH Factor
        print("  - RH Factor 선택")
        rh_factor = patient_data.get("rh_factor", "+")
        down_count = RH_FACTOR_MAP.get(rh_factor, 1)
        self.select_dropdown(PATIENT_DIALOG["dropdown_rh"], down_count)
        time.sleep(1.0)  # 드롭다운 완료 대기
        
        # 6. Gender (맨 마지막에 선택)
        print("  - Gender 선택")
        self.select_gender(patient_data.get("gender", "MALE"))
        time.sleep(1.0)  # 드롭다운 완료 대기
        
        print("[PATIENT] 환자 정보 입력 완료")

    def click_ok_proceed_express_research(self):
        """OK -> PROCEED -> 추가클릭 -> RESEARCH 클릭"""
        print("[WORKFLOW] OK -> PROCEED -> RESEARCH 시퀀스 시작...")
        
        # OK 클릭
        print("  - OK 클릭")
        self.click(PATIENT_DIALOG["btn_ok"])
        print("  - 화면 전환 대기 (2초)...")
        time.sleep(2.0)
        
        # PROCEED 클릭
        print("  - PROCEED 클릭")
        time.sleep(1.0)
        self.click(PATIENT_DIALOG["btn_proceed"])
        time.sleep(1.5)
        
        # 추가 클릭 1
        print("  - 추가 클릭 1 (1714, 286)")
        pyautogui.click(1714, 286)
        time.sleep(1.0)
        
        # 추가 클릭 2
        print("  - 추가 클릭 2 (1652, 642)")
        pyautogui.click(1652, 642)
        time.sleep(3.0)
        
        # RESEARCH 클릭
        print("  - RESEARCH 클릭")
        self.click(PATIENT_DIALOG["btn_research"])
        
        print("[WORKFLOW] 시퀀스 완료 - 스캔 시작됨")

    def capture_results_sequence(self):
        """21페이지 결과 캡쳐"""
        print("[CAPTURE] 21페이지 캡쳐 시작...")
        self.captured_images = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 캡쳐 준비 클릭
        print("  - 캡쳐 준비 클릭 1")
        self.click(RESULT_CAPTURE["btn_before_capture_1"])
        time.sleep(0.5)
        
        print("  - 캡쳐 준비 클릭 2")
        self.click(RESULT_CAPTURE["btn_before_capture_2"])
        time.sleep(0.5)
        
        # 캡쳐 영역 좌표
        x1, y1 = RESULT_CAPTURE["capture_region_start"]
        x2, y2 = RESULT_CAPTURE["capture_region_end"]
        width = x2 - x1
        height = y2 - y1
        
        total_pages = RESULT_CAPTURE["total_pages"]
        
        for page in range(1, total_pages + 1):
            print(f"  - 페이지 {page}/{total_pages} 캡쳐 중...")
            
            # 스크린샷 캡쳐
            screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
            
            # 파일 저장
            filename = f"result_{timestamp}_page{page:02d}.png"
            filepath = self.screenshots_dir / filename
            screenshot.save(str(filepath))
            self.captured_images.append(str(filepath))
            
            print(f"    저장: {filename}")
            
            # 다음 페이지로 (마지막 페이지 제외)
            if page < total_pages:
                pyautogui.press("down")
                time.sleep(TIMING["between_captures"])
        
        print(f"[CAPTURE] 완료: {len(self.captured_images)}개 이미지 저장됨")
        return self.captured_images

    def analyze_captured_results(self):
        """캡쳐된 이미지를 Claude로 분석"""
        print("[ANALYSIS] Claude 분석 시작...")

        if not self.captured_images:
            print("[ANALYSIS] 캡쳐된 이미지가 없습니다.")
            return None

        try:
            import anthropic
            import base64

            load_dotenv(PROJECT_ROOT / ".env")
            api_key = os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                print("[ANALYSIS] ANTHROPIC_API_KEY가 .env에 설정되지 않았습니다.")
                return None

            client = anthropic.Anthropic(api_key=api_key)

            # 이미지를 base64로 변환
            image_contents = []
            for img_path in self.captured_images:
                with open(img_path, "rb") as f:
                    img_data = base64.standard_b64encode(f.read()).decode("utf-8")
                image_contents.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_data,
                    },
                })

            prompt = """You are a bioresonance scan data reader for a clinic in Puebla, Mexico (high altitude, 2,100m).

STRICT RULES:
- ONLY mention levels 4 and 5. Ignore levels 1, 2, 3, and 6 completely.
- Levels 2 and 3 are extremely common at high altitude (Puebla) and are NOT noteworthy.
- DO NOT include any medical disclaimers or recommendations to see a doctor.
- DO NOT mention blood pressure or weight data.
- Use ONLY gentle, simple language that any patient can understand. NO medical jargon.
- NEVER use alarming words like: severo, grave, crítico, peligroso, urgente, daño, deterioro.
- Write as if you are explaining to a friend, not a doctor.

For each organ/system at level 4 or 5, provide:
1. What it means in simple words (why this might happen)
2. Foods that help (specific, easy to find in Mexico)
3. Foods to avoid
4. Simple daily habits to improve

FORMAT (in Spanish):

---
[Organ/System] - Nivel [4 or 5]

Qué significa: [Simple 1-2 sentence explanation a patient can understand]

Alimentos recomendados: [Specific foods available in Mexico that help]

Alimentos a evitar: [Foods that make it worse]

Consejo diario: [One simple lifestyle habit]
---

Example:
---
Estómago - Nivel 4

Qué significa: Su estómago muestra un poco de tensión. Esto puede pasar por comer muy rápido o por estrés.

Alimentos recomendados: Avena, papaya, manzana cocida, caldo de pollo, té de manzanilla.

Alimentos a evitar: Comida muy picante, refrescos, café en exceso, alimentos fritos.

Consejo diario: Coma despacio, mastique bien cada bocado, y tome agua tibia en lugar de fría.
---

If nothing is at level 4 or 5, write only: "Todos los valores están dentro del rango normal. Su cuerpo se encuentra en buen estado."

Respond in Spanish. No preamble, no disclaimers."""

            image_contents.append({"type": "text", "text": prompt})

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": image_contents}],
            )

            result_text = response.content[0].text

            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.reports_dir / f"analysis_{timestamp}.txt"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"NLS 분석 보고서\n")
                f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"분석 이미지 수: {len(self.captured_images)}\n")
                f.write("=" * 50 + "\n\n")
                f.write(result_text)

            print(f"[ANALYSIS] 보고서 저장: {report_path}")
            print("\n" + "=" * 50)
            print("분석 결과:")
            print("=" * 50)
            print(result_text)

            return result_text

        except Exception as e:
            print(f"[ANALYSIS] 오류: {e}")
            return None

    def run_full_workflow(self, patient_data=None):
        """전체 워크플로우 실행 (핫키 대기 포함)"""
        if patient_data is None:
            # Supabase에서 최신 환자 데이터 가져오기
            print("\n[SUPABASE] 최신 환자 데이터 조회 중...")
            patient_data = fetch_latest_patient()
            if patient_data is None:
                print("[ERROR] Supabase에서 환자 데이터를 가져올 수 없습니다.")
                return

        self.current_patient_id = patient_data.get("patient_id")
        save_selected_patient(self.current_patient_id)

        print("\n" + "=" * 60)
        print("NLS 18D CELL Full Automation")
        print("=" * 60)
        
        # 0. NLS 창 활성화
        print("\n[STEP 0] NLS 창 활성화")
        if not self.activate_nls_window():
            print("[ERROR] NLS 프로그램을 먼저 실행해주세요!")
            return
        time.sleep(0.5)
        
        # 1. START 클릭
        print("\n[STEP 1] START 버튼 클릭")
        self.click(START_SCREEN["btn_start"])
        time.sleep(1)
        
        # 2. NEW CARD 클릭
        print("\n[STEP 2] NEW CARD 버튼 클릭")
        self.click(START_SCREEN["btn_new_card"])
        time.sleep(1)
        
        # 3. 환자 정보 입력
        print("\n[STEP 3] 환자 정보 입력")
        self.fill_patient_info(patient_data)
        
        # 4. OK -> PROCEED -> EXPRESS -> RESEARCH
        print("\n[STEP 4] 진행 버튼 클릭")
        self.click_ok_proceed_express_research()
        
        # 5. 핫키 대기 모드
        print("\n" + "=" * 60)
        print("NLS 스캔이 시작되었습니다. (약 11분 소요)")
        print("=" * 60)
        self.wait_for_hotkey_workflow()

    def wait_for_hotkey_workflow(self):
        """핫키 대기 워크플로우"""
        print("\n핫키 대기 중...")
        print(f"  - F9: 21페이지 캡쳐 + Claude 분석 + Supabase 저장")
        print(f"  - ESC: 종료")
        print("-" * 40)

        while self.running:
            if keyboard.is_pressed(HOTKEYS["exit"]):
                print("\n[EXIT] 프로그램 종료")
                self.running = False
                break

            if keyboard.is_pressed(HOTKEYS["trigger_capture"]):
                print(f"\n[HOTKEY] {HOTKEYS['trigger_capture'].upper()} 감지 - 캡쳐 시작")
                time.sleep(0.5)  # 키 릴리즈 대기
                self.capture_results_sequence()
                # 캡쳐 완료 후 바로 Claude 분석
                print("\n[AUTO] 캡쳐 완료 - Claude 분석 자동 시작...")
                result_text = self.analyze_captured_results()
                # 분석 결과 Supabase 저장
                if result_text and self.current_patient_id:
                    save_result_to_supabase(
                        self.current_patient_id,
                        result_text,
                        len(self.captured_images),
                    )
                print("\n핫키 대기 중...")
            
            # (SHIFT+ALT+F9 제거됨 - F9가 캡쳐+분석 모두 수행)
            
            time.sleep(0.1)


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("NLS 18D CELL Full Automation System")
    print("2K Resolution (2560x1440)")
    print("=" * 60)
    
    print("\n옵션을 선택하세요:")
    print("1. 전체 워크플로우 실행 (환자 검색 → NLS 자동 입력 → 스캔)")
    print("2. 핫키 대기 모드만 실행 (스캔 완료 후 캡쳐/분석)")
    print("3. 기존 사용자 삭제 후 전체 실행")
    print("0. 종료")

    choice = input("\n선택 (0-3): ").strip()

    automation = NLSFullAutomation()

    if choice == "1":
        print("\n3초 후 시작합니다. NLS 프로그램이 열려있는지 확인하세요...")
        time.sleep(3)
        automation.run_full_workflow()

    elif choice == "2":
        print("\n[SUPABASE] 환자 검색 중...")
        patient_data = fetch_latest_patient()
        if patient_data:
            automation.current_patient_id = patient_data.get("patient_id")
            save_selected_patient(automation.current_patient_id)
        else:
            print("[WARNING] 환자 데이터 없음 - 분석 결과가 Supabase에 저장되지 않습니다.")
        print("\n핫키 대기 모드 시작...")
        automation.wait_for_hotkey_workflow()

    elif choice == "3":
        print("\n3초 후 시작합니다. NLS 프로그램이 열려있는지 확인하세요...")
        time.sleep(3)
        automation.cleanup_existing_user()
        time.sleep(1)
        automation.run_full_workflow()

    elif choice == "0":
        print("종료합니다.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
