"""
NLS 자동화 메인 모듈
GUI 제어, 화면 캡처, AI 분석을 통합
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from gui_controller import NLSController, NLSActions
from screen_capture import ScreenCapture
from ai_analyzer import AIAnalyzer, AnalysisReport

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/nls_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NLSAutomation:
    """NLS 자동화 통합 클래스"""

    def __init__(self):
        self.window_title = os.getenv("NLS_WINDOW_TITLE", "NLS")
        self.controller = NLSController(self.window_title)
        self.actions = NLSActions(self.controller)
        self.capture = ScreenCapture(os.getenv("SCREENSHOT_DIR", "./screenshots"))
        self.analyzer = AIAnalyzer()
        self.report = AnalysisReport()

        logger.info("NLS 자동화 시스템 초기화 완료")

    def connect(self) -> bool:
        """NLS 프로그램 연결"""
        logger.info(f"NLS 프로그램 찾는 중... (윈도우 제목: {self.window_title})")

        if self.controller.find_window():
            logger.info("NLS 프로그램 발견")
            self.controller.activate_window()
            return True

        logger.error("NLS 프로그램을 찾을 수 없습니다")
        return False

    def capture_and_analyze(self, custom_prompt: Optional[str] = None) -> dict:
        """현재 화면 캡처 및 AI 분석"""
        logger.info("화면 캡처 시작...")

        # 윈도우 캡처
        image_path = self.capture.capture_nls_window(self.window_title)

        if not image_path:
            # 윈도우 캡처 실패 시 전체 화면 캡처
            logger.warning("윈도우 캡처 실패, 전체 화면 캡처로 전환")
            image_path = self.capture.capture_full_screen()

        logger.info(f"캡처 완료: {image_path}")

        # AI 분석
        logger.info("AI 분석 시작...")
        if custom_prompt:
            result = self.analyzer.analyze_image(image_path, custom_prompt)
        else:
            result = self.analyzer.analyze_nls_scan(image_path)

        result["image_path"] = image_path
        logger.info("AI 분석 완료")

        return result

    def run_scan_sequence(
        self,
        pages: int = 5,
        delay: float = 2.0
    ) -> list[dict]:
        """여러 페이지 순차 스캔 및 분석"""
        results = []

        logger.info(f"스캔 시퀀스 시작 (총 {pages} 페이지)")

        for i in range(pages):
            logger.info(f"페이지 {i + 1}/{pages} 처리 중...")

            # 화면 안정화 대기
            time.sleep(delay)

            # 캡처 및 분석
            result = self.capture_and_analyze()
            result["page"] = i + 1
            results.append(result)

            # 다음 페이지로 이동 (마지막 페이지 제외)
            if i < pages - 1:
                self.actions.next_page()

        logger.info("스캔 시퀀스 완료")
        return results

    def auto_scan_with_report(
        self,
        pages: int = 5,
        patient_info: Optional[dict] = None
    ) -> str:
        """자동 스캔 후 리포트 생성"""
        # NLS 연결 확인
        if not self.connect():
            raise RuntimeError("NLS 프로그램에 연결할 수 없습니다")

        # 스캔 실행
        results = self.run_scan_sequence(pages)

        # 리포트 생성
        report_path = self.report.generate_report(results, patient_info)
        logger.info(f"리포트 생성 완료: {report_path}")

        # 요약 출력
        summary = self.report.generate_summary(results)
        print("\n" + "=" * 50)
        print("분석 요약")
        print("=" * 50)
        print(summary)

        return report_path

    def interactive_mode(self):
        """대화형 모드"""
        print("\n=== NLS 자동화 시스템 ===")
        print("명령어:")
        print("  c  - 현재 화면 캡처 및 분석")
        print("  s  - 스캔 시퀀스 시작")
        print("  n  - 다음 페이지")
        print("  p  - 이전 페이지")
        print("  r  - 리포트 생성")
        print("  q  - 종료")
        print()

        results = []

        while True:
            cmd = input("명령 입력 > ").strip().lower()

            if cmd == 'q':
                print("종료합니다.")
                break

            elif cmd == 'c':
                if self.connect():
                    result = self.capture_and_analyze()
                    results.append(result)
                    print(f"\n분석 결과:\n{result['analysis']}\n")

            elif cmd == 's':
                if self.connect():
                    pages = input("페이지 수 (기본 5): ").strip()
                    pages = int(pages) if pages else 5
                    results = self.run_scan_sequence(pages)
                    print(f"\n{len(results)}개 페이지 분석 완료\n")

            elif cmd == 'n':
                if self.connect():
                    self.actions.next_page()
                    print("다음 페이지로 이동")

            elif cmd == 'p':
                if self.connect():
                    self.actions.prev_page()
                    print("이전 페이지로 이동")

            elif cmd == 'r':
                if results:
                    report_path = self.report.generate_report(results)
                    print(f"리포트 저장됨: {report_path}")
                else:
                    print("분석 결과가 없습니다. 먼저 캡처(c) 또는 스캔(s)을 실행하세요.")

            else:
                print("알 수 없는 명령어입니다.")


def main():
    """메인 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description="NLS 프로그램 자동화")
    parser.add_argument(
        "--mode",
        choices=["interactive", "auto", "single"],
        default="interactive",
        help="실행 모드"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=5,
        help="자동 스캔 페이지 수"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./reports",
        help="리포트 저장 경로"
    )

    args = parser.parse_args()

    # 로그 디렉토리 생성
    Path("logs").mkdir(exist_ok=True)

    automation = NLSAutomation()

    if args.mode == "interactive":
        automation.interactive_mode()

    elif args.mode == "auto":
        report_path = automation.auto_scan_with_report(args.pages)
        print(f"자동 스캔 완료. 리포트: {report_path}")

    elif args.mode == "single":
        if automation.connect():
            result = automation.capture_and_analyze()
            print(f"\n분석 결과:\n{result['analysis']}")


if __name__ == "__main__":
    main()
