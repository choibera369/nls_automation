"""
NLS 18D CELL NLS 워크플로우 자동화
실제 UI 스크린샷 기반으로 작성
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

import pyautogui
from dotenv import load_dotenv

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gui_controller import NLSController
from src.screen_capture import ScreenCapture
from src.ai_analyzer import AIAnalyzer
from nls_config.nls_config import (
    PROGRAM_INFO, MARKER_STATUS, BODY_PART_TCM_MAP,
    START_SCREEN, CARD_SCREEN, PATIENT_DIALOG, RESEARCH_SCREEN, SCAN_SCREEN,
    TIMING, HOTKEYS
)

load_dotenv()


@dataclass
class PatientInfo:
    """환자 정보"""
    last_name: str
    first_name: str
    middle_name: str = ""
    birth_date: str = ""      # YYYY-MM-DD
    gender: str = "MALE"      # MALE, FEMALE
    blood_type: str = "I(O)"  # I(O), II(A), III(B), IV(AB)
    rh_factor: str = "+"      # +, -
    address: str = ""
    phone: str = ""
    email: str = ""


@dataclass
class ScanResult:
    """검사 결과"""
    body_part: str              # 검사 부위명 (영문)
    body_part_kr: str           # 검사 부위명 (한글)
    markers: dict               # {1: count, 2: count, ...}
    warning_count: int          # 3-5 마커 총 개수
    critical_count: int         # 6 마커 개수
    n_spin: Optional[float]
    s_spin: Optional[float]
    f_value: Optional[float]
    q_value: Optional[float]
    tcm_info: dict              # 한의학 정보
    timestamp: str
    image_path: str
    ai_analysis: dict


class NLSWorkflow:
    """NLS 18D CELL NLS 자동화 워크플로우"""

    def __init__(self):
        self.controller = NLSController(PROGRAM_INFO["window_title"])
        self.capture = ScreenCapture("./screenshots")
        self.analyzer = AIAnalyzer()
        self.results: list[ScanResult] = []
        self.current_patient: Optional[PatientInfo] = None

        # 디렉토리 생성
        Path("./screenshots").mkdir(exist_ok=True)
        Path("./reports").mkdir(exist_ok=True)
        Path("./logs").mkdir(exist_ok=True)

    # ============================================================
    # 프로그램 실행 및 연결
    # ============================================================
    def launch_nls(self, exe_path: str = None) -> bool:
        """NLS 프로그램 실행"""
        if exe_path is None:
            # 기본 경로 (환경변수 또는 설정에서)
            exe_path = os.getenv("NLS_EXE_PATH", r"C:\Program Files\18D CELL NLS\18D CELL NLS.exe")

        exe_path = Path(exe_path)
        if not exe_path.exists():
            print(f"[!] NLS 실행 파일을 찾을 수 없습니다: {exe_path}")
            print("    .env 파일에 NLS_EXE_PATH를 설정하세요.")
            return False

        print(f"[*] NLS 프로그램 실행 중... {exe_path}")
        try:
            subprocess.Popen(str(exe_path), shell=True)
            time.sleep(TIMING["startup_wait"])
            print("[+] NLS 프로그램 실행됨")
            return True
        except Exception as e:
            print(f"[!] 실행 실패: {e}")
            return False

    def connect(self, auto_launch: bool = True) -> bool:
        """NLS 프로그램 연결 (없으면 자동 실행)"""
        print(f"[*] {PROGRAM_INFO['name']} 프로그램 찾는 중...")

        if not self.controller.find_window():
            if auto_launch:
                print("[*] 프로그램이 실행되지 않음. 자동 실행 시도...")
                if not self.launch_nls():
                    return False
                time.sleep(TIMING["startup_wait"])
                if not self.controller.find_window():
                    print("[!] 프로그램 실행 후에도 찾을 수 없습니다.")
                    return False
            else:
                print("[!] 프로그램을 찾을 수 없습니다. 먼저 실행하세요.")
                return False

        self.controller.activate_window()
        time.sleep(TIMING["click_interval"])
        print("[+] 프로그램 연결됨")
        return True

    # ============================================================
    # 시작 화면
    # ============================================================
    def click_start(self):
        """시작 화면에서 START 클릭"""
        print("[*] START 클릭...")
        self._click_at("START", START_SCREEN["btn_start"], image="btn_start.png")
        time.sleep(TIMING["page_load"])

    # ============================================================
    # 환자 카드 관리
    # ============================================================
    def create_new_card(self, patient: PatientInfo):
        """새 환자 카드 생성"""
        self.current_patient = patient
        print(f"[*] 새 환자 카드 생성: {patient.last_name} {patient.first_name}")

        # NEW CARD 버튼 클릭
        self._click_at("NEW CARD", CARD_SCREEN["btn_new_card"], image="btn_new_card.png")
        time.sleep(TIMING["dialog_wait"])

        # 환자 정보 입력 다이얼로그
        self._fill_patient_dialog(patient)

        # OK 버튼 클릭
        self._click_at("OK", PATIENT_DIALOG["btn_ok"], image="btn_ok.png")
        time.sleep(TIMING["page_load"])
        print("[+] 환자 카드 생성 완료")

    def _fill_patient_dialog(self, patient: PatientInfo):
        """환자 정보 입력 다이얼로그 채우기"""
        # Last Name
        self._click_at("LAST NAME", PATIENT_DIALOG["input_last_name"])
        self._clear_and_type(patient.last_name)

        # First Name
        self._click_at("FIRST NAME", PATIENT_DIALOG["input_first_name"])
        self._clear_and_type(patient.first_name)

        # Middle Name
        if patient.middle_name:
            self._click_at("MIDDLE NAME", PATIENT_DIALOG["input_middle_name"])
            self._clear_and_type(patient.middle_name)

        # Birth Date
        if patient.birth_date:
            self._click_at("BIRTH DATE", PATIENT_DIALOG["input_birth_date"])
            self._clear_and_type(patient.birth_date)

        # Gender (드롭다운)
        self._click_at("GENDER", PATIENT_DIALOG["dropdown_gender"])
        time.sleep(0.2)
        if patient.gender == "FEMALE":
            pyautogui.press("down")
        pyautogui.press("enter")

        # Blood Type (드롭다운)
        self._click_at("BLOOD TYPE", PATIENT_DIALOG["dropdown_blood_type"])
        time.sleep(0.2)
        blood_types = ["I(O)", "II(A)", "III(B)", "IV(AB)"]
        idx = blood_types.index(patient.blood_type) if patient.blood_type in blood_types else 0
        for _ in range(idx):
            pyautogui.press("down")
        pyautogui.press("enter")

        # RH Factor (드롭다운)
        self._click_at("RH", PATIENT_DIALOG["dropdown_rh"])
        time.sleep(0.2)
        if patient.rh_factor == "-":
            pyautogui.press("down")
        pyautogui.press("enter")

        # Address
        if patient.address:
            self._click_at("ADDRESS", PATIENT_DIALOG["input_address"])
            self._clear_and_type(patient.address)

        # Phone
        if patient.phone:
            self._click_at("PHONE", PATIENT_DIALOG["input_phone"])
            self._clear_and_type(patient.phone)

        # Email
        if patient.email:
            self._click_at("EMAIL", PATIENT_DIALOG["input_email"])
            self._clear_and_type(patient.email)

    def select_existing_card(self, search_name: str):
        """기존 환자 카드 선택"""
        print(f"[*] 환자 검색: {search_name}")

        # 검색창에 이름 입력
        self._click_at("SEARCH", CARD_SCREEN["input_search"])
        self._clear_and_type(search_name)
        pyautogui.press("enter")
        time.sleep(TIMING["page_load"])

        # SELECT CARD 클릭
        self._click_at("SELECT CARD", CARD_SCREEN["btn_select_card"])
        time.sleep(TIMING["dialog_wait"])

    # ============================================================
    # 검사 실행
    # ============================================================
    def start_research(self):
        """검사 시작 (RESEARCH 버튼 클릭)"""
        print("[*] RESEARCH 클릭...")
        self._click_at("RESEARCH", CARD_SCREEN["btn_research"], image="btn_research.png")
        time.sleep(TIMING["page_load"])

    def select_research_type(self, research_name: str = None):
        """검사 유형 선택"""
        print("[*] 검사 유형 선택 화면")

        # 검사 목록에서 첫 번째 항목 클릭 (또는 특정 항목 검색)
        if research_name:
            # 목록에서 해당 항목 찾아서 클릭
            self._click_at("RESEARCH LIST", RESEARCH_SCREEN["research_list_first_item"])
        else:
            # 첫 번째 항목 선택
            self._click_at("FIRST ITEM", RESEARCH_SCREEN["research_list_first_item"])

        time.sleep(TIMING["click_interval"])

        # RESEARCH 버튼 클릭하여 검사 시작
        self._click_at("START RESEARCH", RESEARCH_SCREEN["btn_research"])
        time.sleep(TIMING["page_load"])

    # ============================================================
    # 화면 캡처 및 AI 분석
    # ============================================================
    def capture_current_screen(self) -> str:
        """현재 화면 캡처"""
        image_path = self.capture.capture_nls_window(PROGRAM_INFO["window_title"])
        if not image_path:
            image_path = self.capture.capture_full_screen()
        print(f"[+] 캡처: {image_path}")
        return image_path

    def analyze_scan_image(self, image_path: str) -> dict:
        """AI로 스캔 이미지 분석"""
        print("[*] AI 분석 중...")

        prompt = self._get_analysis_prompt()
        result = self.analyzer.analyze_image(image_path, prompt)

        # JSON 파싱 시도
        try:
            analysis_text = result.get("analysis", "")
            if "```json" in analysis_text:
                json_start = analysis_text.index("```json") + 7
                json_end = analysis_text.index("```", json_start)
                json_str = analysis_text[json_start:json_end].strip()
                result["parsed"] = json.loads(json_str)
            elif "{" in analysis_text:
                json_start = analysis_text.index("{")
                json_end = analysis_text.rindex("}") + 1
                json_str = analysis_text[json_start:json_end]
                result["parsed"] = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            result["parsed"] = None

        print("[+] 분석 완료")
        return result

    def _get_analysis_prompt(self) -> str:
        """NLS 분석용 프롬프트"""
        return """
이 NLS 18D CELL NLS 생체공명 검사 화면을 분석해주세요.

## 마커 해석
- 노란 육각형 (숫자 1, 2): 정상/양호 상태
- 빨간 삼각형 (숫자 3, 4, 5): 주의/경고 필요
- 검정 사각형 (숫자 6): 심각한 이상

## 분석 요청
1. 화면 하단의 검사 부위명 읽기
2. 이미지에서 보이는 모든 숫자 마커 개수 세기
3. 우측 패널의 N spin, S spin, F, Q 값 읽기
4. 3 이상 마커가 있는 위치 설명
5. 한의학적 해석 (해당 부위의 장부/경락 연관성)

## 응답 형식 (JSON)
```json
{
    "body_part": "검사 부위명 (영문, 화면에서 읽은 그대로)",
    "body_part_kr": "검사 부위명 (한국어 번역)",
    "markers": {
        "1": 개수,
        "2": 개수,
        "3": 개수,
        "4": 개수,
        "5": 개수,
        "6": 개수
    },
    "total_markers": 전체 마커 수,
    "warning_markers": 3-5 마커 총 개수,
    "critical_markers": 6 마커 개수,
    "n_spin": 값 또는 null,
    "s_spin": 값 또는 null,
    "f_value": 값 또는 null,
    "q_value": 값 또는 null,
    "dominated_spin": "N" 또는 "S",
    "problem_areas": ["문제 영역 설명"],
    "tcm_interpretation": {
        "organ": "관련 장부 (한의학)",
        "meridian": "관련 경락",
        "element": "오행 속성",
        "diagnosis": "한의학적 진단 의견"
    },
    "overall_status": "양호/주의/경고/위험",
    "recommendations": ["권장사항"]
}
```
"""

    def capture_and_analyze(self) -> dict:
        """캡처 + 분석 한 번에"""
        image_path = self.capture_current_screen()
        analysis = self.analyze_scan_image(image_path)
        return {
            "image_path": image_path,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    # ============================================================
    # 스캔 시퀀스
    # ============================================================
    def run_scan_sequence(self, pages: int = 5, delay: float = None) -> list[dict]:
        """여러 페이지 순차 스캔"""
        if delay is None:
            delay = TIMING["scan_delay"]

        results = []
        print(f"\n[*] 스캔 시퀀스 시작 ({pages} 페이지)")
        print("=" * 50)

        for i in range(pages):
            print(f"\n[{i+1}/{pages}] 페이지 처리 중...")

            # 화면 안정화 대기
            time.sleep(delay)

            # 캡처 및 분석
            result = self.capture_and_analyze()
            result["page"] = i + 1
            results.append(result)

            # 간단 출력
            parsed = result.get("analysis", {}).get("parsed")
            if parsed:
                status = parsed.get("overall_status", "알 수 없음")
                body_part = parsed.get("body_part_kr", parsed.get("body_part", ""))
                warning = parsed.get("warning_markers", 0)
                print(f"    부위: {body_part}")
                print(f"    상태: {status}, 경고마커: {warning}개")

            # 다음 페이지 (마지막 제외)
            if i < pages - 1:
                self._next_page()

        print("\n" + "=" * 50)
        print(f"[+] 스캔 완료: {len(results)} 페이지")
        return results

    def _next_page(self):
        """다음 페이지로 이동"""
        pyautogui.press(HOTKEYS["next_page"])
        time.sleep(TIMING["click_interval"])

    def _prev_page(self):
        """이전 페이지로 이동"""
        pyautogui.press(HOTKEYS["prev_page"])
        time.sleep(TIMING["click_interval"])

    # ============================================================
    # 리포트 생성
    # ============================================================
    def generate_tcm_report(self, results: list[dict]) -> dict:
        """한의학적 종합 리포트 생성"""
        print("[*] 종합 리포트 생성 중...")

        # 분석 결과 요약
        summaries = []
        total_warnings = 0
        total_criticals = 0
        problem_parts = []

        for r in results:
            parsed = r.get("analysis", {}).get("parsed")
            if parsed:
                summaries.append(parsed)
                total_warnings += parsed.get("warning_markers", 0)
                total_criticals += parsed.get("critical_markers", 0)
                if parsed.get("warning_markers", 0) > 0 or parsed.get("critical_markers", 0) > 0:
                    problem_parts.append({
                        "part": parsed.get("body_part_kr", parsed.get("body_part")),
                        "warnings": parsed.get("warning_markers", 0),
                        "criticals": parsed.get("critical_markers", 0),
                        "tcm": parsed.get("tcm_interpretation", {})
                    })

        report = {
            "patient": asdict(self.current_patient) if self.current_patient else None,
            "scan_date": datetime.now().isoformat(),
            "total_pages": len(results),
            "summary": {
                "total_warning_markers": total_warnings,
                "total_critical_markers": total_criticals,
                "problem_parts": problem_parts
            },
            "individual_results": results,
            "tcm_summary": self._generate_tcm_summary(summaries)
        }

        print("[+] 리포트 생성 완료")
        return report

    def _generate_tcm_summary(self, summaries: list[dict]) -> dict:
        """한의학 종합 요약"""
        organs_affected = set()
        meridians_affected = set()
        elements_affected = set()

        for s in summaries:
            tcm = s.get("tcm_interpretation", {})
            if tcm.get("organ"):
                organs_affected.add(tcm["organ"])
            if tcm.get("meridian"):
                meridians_affected.add(tcm["meridian"])
            if tcm.get("element"):
                elements_affected.add(tcm["element"])

        return {
            "affected_organs": list(organs_affected),
            "affected_meridians": list(meridians_affected),
            "affected_elements": list(elements_affected),
            "treatment_suggestion": self._suggest_treatment(organs_affected, elements_affected)
        }

    def _suggest_treatment(self, organs: set, elements: set) -> list[str]:
        """치료 제안"""
        suggestions = []

        if "신(腎)" in str(organs):
            suggestions.append("신장 보양: 태계(太谿), 복류(復溜) 자침")
        if "간(肝)" in str(organs):
            suggestions.append("간기 소통: 태충(太衝), 기문(期門) 자침")
        if "비(脾)" in str(organs) or "위(胃)" in str(organs):
            suggestions.append("비위 보강: 족삼리(足三里), 삼음교(三陰交) 자침")
        if "심(心)" in str(organs):
            suggestions.append("심기 안정: 신문(神門), 내관(內關) 자침")
        if "폐(肺)" in str(organs):
            suggestions.append("폐기 보충: 폐수(肺兪), 태연(太淵) 자침")

        if not suggestions:
            suggestions.append("전반적 기혈 조절: 합곡(合谷), 족삼리(足三里), 삼음교(三陰交)")

        return suggestions

    def save_report(self, report: dict, filename: str = None) -> str:
        """리포트 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            patient_name = ""
            if self.current_patient:
                patient_name = f"{self.current_patient.last_name}_{self.current_patient.first_name}_"
            filename = f"nls_report_{patient_name}{timestamp}.json"

        filepath = Path("./reports") / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"[+] 리포트 저장: {filepath}")

        # HTML 리포트도 생성
        html_path = self._generate_html_report(report, filepath.stem)
        print(f"[+] HTML 리포트: {html_path}")

        return str(filepath)

    def _generate_html_report(self, report: dict, basename: str) -> str:
        """한의사용 HTML 리포트 생성"""
        patient = report.get("patient") or {}
        summary = report.get("summary", {})
        tcm = report.get("tcm_summary", {})

        # 문제 부위 테이블
        problem_rows = ""
        for p in summary.get("problem_parts", []):
            tcm_info = p.get("tcm", {})
            problem_rows += f"""
            <tr>
                <td>{p.get('part', 'N/A')}</td>
                <td class="warning">{p.get('warnings', 0)}</td>
                <td class="critical">{p.get('criticals', 0)}</td>
                <td>{tcm_info.get('organ', 'N/A')}</td>
                <td>{tcm_info.get('meridian', 'N/A')}</td>
            </tr>"""

        # 치료 제안
        treatment_list = ""
        for t in tcm.get("treatment_suggestion", []):
            treatment_list += f"<li>{t}</li>"

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>NLS 검사 결과 - {patient.get('last_name', '')} {patient.get('first_name', '')}</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .patient-info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary-box {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card.warning {{ background: #fff3cd; border: 2px solid #ffc107; }}
        .stat-card.critical {{ background: #f8d7da; border: 2px solid #dc3545; }}
        .stat-card h3 {{ margin: 0; font-size: 36px; }}
        .stat-card p {{ margin: 5px 0 0; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .warning {{ color: #856404; font-weight: bold; }}
        .critical {{ color: #721c24; font-weight: bold; }}
        .treatment {{ background: #d4edda; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .treatment h2 {{ color: #155724; margin-top: 0; }}
        .treatment ul {{ margin: 0; padding-left: 20px; }}
        .treatment li {{ margin: 8px 0; }}
        .footer {{ margin-top: 30px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 NLS 생체공명 검사 결과</h1>

        <div class="patient-info">
            <strong>환자:</strong> {patient.get('last_name', '')} {patient.get('first_name', '')} |
            <strong>생년월일:</strong> {patient.get('birth_date', 'N/A')} |
            <strong>혈액형:</strong> {patient.get('blood_type', 'N/A')} {patient.get('rh_factor', '')} |
            <strong>검사일:</strong> {report.get('scan_date', '')[:10]}
        </div>

        <h2>📊 검사 요약</h2>
        <div class="summary-box">
            <div class="stat-card warning">
                <h3>{summary.get('total_warning_markers', 0)}</h3>
                <p>주의 마커 (3-5)</p>
            </div>
            <div class="stat-card critical">
                <h3>{summary.get('total_critical_markers', 0)}</h3>
                <p>심각 마커 (6)</p>
            </div>
        </div>

        <h2>⚠️ 이상 부위</h2>
        <table>
            <tr>
                <th>검사 부위</th>
                <th>주의 마커</th>
                <th>심각 마커</th>
                <th>관련 장부</th>
                <th>관련 경락</th>
            </tr>
            {problem_rows if problem_rows else '<tr><td colspan="5" style="text-align:center;">이상 소견 없음</td></tr>'}
        </table>

        <div class="treatment">
            <h2>💉 한의학적 치료 제안</h2>
            <ul>
                {treatment_list if treatment_list else '<li>전반적 기혈 조절: 합곡(合谷), 족삼리(足三里), 삼음교(三陰交)</li>'}
            </ul>
        </div>

        <h2>🔮 영향받은 오행</h2>
        <p><strong>장부:</strong> {', '.join(tcm.get('affected_organs', [])) or '해당 없음'}</p>
        <p><strong>경락:</strong> {', '.join(tcm.get('affected_meridians', [])) or '해당 없음'}</p>
        <p><strong>오행:</strong> {', '.join(tcm.get('affected_elements', [])) or '해당 없음'}</p>

        <div class="footer">
            NLS 자동화 시스템 | AI 분석 결과 (참고용) | {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</body>
</html>"""

        html_path = Path("./reports") / f"{basename}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        return str(html_path)

    def notify_doctor(self, report: dict, method: str = "popup"):
        """한의사에게 결과 알림"""
        patient = report.get("patient") or {}
        summary = report.get("summary", {})

        patient_name = f"{patient.get('last_name', '')} {patient.get('first_name', '')}".strip() or "환자"
        warnings = summary.get("total_warning_markers", 0)
        criticals = summary.get("total_critical_markers", 0)

        # 요약 메시지
        if criticals > 0:
            status = "🔴 심각한 이상 발견"
        elif warnings > 0:
            status = "🟡 주의 필요"
        else:
            status = "🟢 정상"

        message = f"""
{'='*50}
  NLS 검사 완료 알림
{'='*50}
환자: {patient_name}
상태: {status}
주의 마커: {warnings}개
심각 마커: {criticals}개

문제 부위:
"""
        for p in summary.get("problem_parts", [])[:5]:
            message += f"  - {p.get('part', 'N/A')}: 경고 {p.get('warnings', 0)}, 심각 {p.get('criticals', 0)}\n"

        message += f"\n리포트: ./reports/ 폴더 확인\n{'='*50}"

        print(message)

        # 팝업 알림 (Windows)
        if method == "popup":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"환자: {patient_name}\n상태: {status}\n주의: {warnings}개, 심각: {criticals}개",
                    "NLS 검사 완료",
                    0x40  # MB_ICONINFORMATION
                )
            except Exception as e:
                print(f"[!] 팝업 알림 실패: {e}")

        # HTML 리포트 자동 열기
        if method in ("popup", "browser"):
            try:
                import webbrowser
                report_files = sorted(Path("./reports").glob("*.html"), reverse=True)
                if report_files:
                    webbrowser.open(str(report_files[0]))
            except Exception as e:
                print(f"[!] 브라우저 열기 실패: {e}")

    # ============================================================
    # 유틸리티
    # ============================================================
    def _click_at(self, name: str, coords: tuple = None, image: str = None):
        """
        클릭 (이미지 기반 우선, 실패시 좌표 사용)

        Args:
            name: 버튼 이름 (로깅용)
            coords: 좌표 (x, y) - 폴백용
            image: 이미지 파일명 (예: "btn_start.png")
        """
        images_dir = Path(__file__).parent.parent / "images"

        # 1. 이미지 기반 클릭 시도
        if image:
            image_path = images_dir / image
            if image_path.exists():
                try:
                    location = pyautogui.locateCenterOnScreen(
                        str(image_path),
                        confidence=0.8
                    )
                    if location:
                        print(f"    클릭: {name} (이미지 매칭: {location.x}, {location.y})")
                        pyautogui.click(location)
                        time.sleep(TIMING["click_interval"])
                        return True
                except Exception as e:
                    print(f"    이미지 매칭 실패: {e}")

        # 2. 좌표 기반 클릭 (폴백)
        if coords:
            x, y = coords[0], coords[1]
            print(f"    클릭: {name} (좌표: {x}, {y})")
            pyautogui.click(x, y)
            time.sleep(TIMING["click_interval"])
            return True

        print(f"    [!] 클릭 실패: {name}")
        return False

    def _clear_and_type(self, text: str):
        """필드 지우고 입력"""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        pyautogui.typewrite(text, interval=TIMING["input_interval"])

    def exit_scan(self):
        """검사 화면 종료"""
        self._click_at("EXIT", SCAN_SCREEN["btn_exit"], image="btn_exit.png")
        time.sleep(TIMING["page_load"])


# ============================================================
# 완전 자동화 모드
# ============================================================
def run_full_automation(patient_info: dict = None, pages: int = 5):
    """
    완전 자동화 실행
    NLS 실행 → 환자 등록 → 검사 → 분석 → 리포트 → 알림
    """
    workflow = NLSWorkflow()

    print("\n" + "=" * 60)
    print("  🤖 NLS 완전 자동화 모드")
    print("=" * 60)

    # 1. NLS 프로그램 실행 및 연결
    print("\n[1/6] NLS 프로그램 실행...")
    if not workflow.connect(auto_launch=True):
        print("[!] 프로그램 연결 실패")
        return None

    # 2. 시작 화면에서 START 클릭
    print("\n[2/6] 프로그램 시작...")
    workflow.click_start()

    # 3. 환자 정보 입력
    print("\n[3/6] 환자 카드 생성...")
    if patient_info:
        patient = PatientInfo(**patient_info)
    else:
        # 기본 테스트 환자
        patient = PatientInfo(
            last_name="Test",
            first_name="Patient",
            birth_date="1990-01-01",
            gender="MALE",
            blood_type="I(O)"
        )
    workflow.create_new_card(patient)

    # 4. 검사 시작
    print("\n[4/6] 검사 시작...")
    workflow.start_research()
    workflow.select_research_type()

    # 5. 스캔 및 AI 분석
    print(f"\n[5/6] 스캔 및 AI 분석 ({pages} 페이지)...")
    results = workflow.run_scan_sequence(pages)

    # 6. 리포트 생성 및 알림
    print("\n[6/6] 리포트 생성 및 한의사 알림...")
    report = workflow.generate_tcm_report(results)
    workflow.save_report(report)
    workflow.notify_doctor(report, method="popup")

    print("\n" + "=" * 60)
    print("  ✅ 자동화 완료!")
    print("=" * 60)

    return report


# ============================================================
# 메인 실행
# ============================================================
def main():
    """메인 실행"""
    workflow = NLSWorkflow()

    print("\n" + "=" * 50)
    print("  NLS 18D CELL NLS 자동화 시스템")
    print("=" * 50)
    print("\n메뉴:")
    print("  1. 🤖 완전 자동화 (새 환자)")
    print("  2. 전체 워크플로우 (수동 입력)")
    print("  3. 현재 화면 캡처/분석")
    print("  4. 연속 스캔 (현재 검사)")
    print("  5. 종료")

    while True:
        choice = input("\n선택 > ").strip()

        if choice == "1":
            # 완전 자동화 모드
            print("\n[환자 정보 입력] (Enter로 기본값 사용)")
            last_name = input("성 (Last Name) [Test]: ").strip() or "Test"
            first_name = input("이름 (First Name) [Patient]: ").strip() or "Patient"
            birth = input("생년월일 (YYYY-MM-DD) [1990-01-01]: ").strip() or "1990-01-01"
            pages = int(input("스캔 페이지 수 [5]: ").strip() or "5")

            patient_info = {
                "last_name": last_name,
                "first_name": first_name,
                "birth_date": birth,
                "gender": "MALE",
                "blood_type": "I(O)"
            }

            run_full_automation(patient_info, pages)

        elif choice == "2":
            # 수동 워크플로우
            if not workflow.connect():
                continue

            print("\n[환자 정보 입력]")
            last_name = input("성 (Last Name): ").strip() or "Test"
            first_name = input("이름 (First Name): ").strip() or "Patient"
            birth = input("생년월일 (YYYY-MM-DD): ").strip() or "1990-01-01"
            gender = input("성별 (MALE/FEMALE): ").strip().upper() or "MALE"
            blood = input("혈액형 (I(O)/II(A)/III(B)/IV(AB)): ").strip() or "I(O)"

            patient = PatientInfo(
                last_name=last_name,
                first_name=first_name,
                birth_date=birth,
                gender=gender,
                blood_type=blood
            )

            workflow.click_start()
            workflow.create_new_card(patient)
            workflow.start_research()
            workflow.select_research_type()

            pages = int(input("스캔 페이지 수 (기본 5): ").strip() or "5")
            results = workflow.run_scan_sequence(pages)

            report = workflow.generate_tcm_report(results)
            workflow.save_report(report)
            workflow.notify_doctor(report)

        elif choice == "3":
            # 현재 화면 캡처/분석
            if workflow.connect(auto_launch=False):
                result = workflow.capture_and_analyze()
                parsed = result.get("analysis", {}).get("parsed")
                if parsed:
                    print(f"\n부위: {parsed.get('body_part_kr', 'N/A')}")
                    print(f"상태: {parsed.get('overall_status', 'N/A')}")
                    print(f"경고 마커: {parsed.get('warning_markers', 0)}개")
                    tcm = parsed.get("tcm_interpretation", {})
                    if tcm:
                        print(f"장부: {tcm.get('organ', 'N/A')}")
                        print(f"경락: {tcm.get('meridian', 'N/A')}")
                else:
                    print(result.get("analysis", {}).get("analysis", "분석 실패"))

        elif choice == "4":
            # 연속 스캔
            if workflow.connect(auto_launch=False):
                pages = int(input("페이지 수: ").strip() or "5")
                results = workflow.run_scan_sequence(pages)
                report = workflow.generate_tcm_report(results)
                workflow.save_report(report)
                workflow.notify_doctor(report)

        elif choice == "5":
            print("종료합니다.")
            break

        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
