"""
AI 이미지 분석 모듈
Google Gemini Vision API를 사용하여 NLS 검사 화면 분석
"""

import os
import base64
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class AIAnalyzer:
    """AI 기반 이미지 분석 클래스 (Gemini)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API 키가 필요합니다. .env 파일에 GEMINI_API_KEY를 설정하세요.")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"

    def analyze_image(
        self,
        image_path: str,
        prompt: str = "이 이미지를 분석해주세요."
    ) -> dict:
        """이미지 분석"""
        # 이미지 로드
        img = Image.open(image_path)

        # 이미지를 bytes로 변환
        import io
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        # Gemini에 요청 (새 API)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    ]
                )
            ]
        )

        return {
            "analysis": response.text,
            "model": self.model_name,
            "timestamp": datetime.now().isoformat()
        }

    def analyze_nls_scan(self, image_path: str) -> dict:
        """NLS 검사 화면 전용 분석"""
        prompt = """
이 NLS(Nonlinear Analysis System) 생체공명 검사 화면을 분석해주세요.

## 마커 해석 기준
- 숫자 1, 2 (노란색 육각형): 정상/양호 상태
- 숫자 3, 4, 5 (빨간색 삼각형): 이상 징후/주의 필요
- 숫자 6 (검정색 사각형): 심각한 이상

## 분석 항목
1. 검사 부위 (화면 하단 텍스트 확인)
2. 보이는 모든 숫자 마커 (1-6) 개수와 분포
3. 경고 마커(3-6) 위치와 개수
4. N spin / S spin 값 (우측 패널)
5. F, Q 수치 (우측 패널)

## 한의학적 해석
- 해당 부위와 연관된 장부(臟腑)
- 관련 경락(經絡)
- 오행(五行) 속성

JSON 형식으로 반환:
{
    "body_part": "영문 부위명",
    "body_part_kr": "한국어 부위명",
    "markers": {
        "normal": 1-2 마커 개수,
        "warning": 3-5 마커 개수,
        "critical": 6 마커 개수
    },
    "n_spin": 값 또는 null,
    "s_spin": 값 또는 null,
    "f_value": 값 또는 null,
    "q_value": 값 또는 null,
    "tcm": {
        "organ": "관련 장부",
        "meridian": "관련 경락",
        "element": "오행 속성"
    },
    "status": "정상/주의/경고/위험",
    "recommendations": ["권장사항"]
}
        """

        result = self.analyze_image(image_path, prompt)

        # JSON 파싱 시도
        try:
            analysis_text = result["analysis"]
            # JSON 블록 추출
            if "```json" in analysis_text:
                json_start = analysis_text.index("```json") + 7
                json_end = analysis_text.index("```", json_start)
                json_str = analysis_text[json_start:json_end].strip()
            elif "{" in analysis_text:
                json_start = analysis_text.index("{")
                json_end = analysis_text.rindex("}") + 1
                json_str = analysis_text[json_start:json_end]
            else:
                json_str = None

            if json_str:
                result["structured_analysis"] = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            result["structured_analysis"] = None

        return result

    def compare_scans(
        self,
        before_image: str,
        after_image: str
    ) -> dict:
        """두 검사 화면 비교 분석"""
        import io

        img1 = Image.open(before_image)
        img2 = Image.open(after_image)

        # 이미지를 bytes로 변환
        img1_bytes = io.BytesIO()
        img1.save(img1_bytes, format='PNG')
        img1_data = img1_bytes.getvalue()

        img2_bytes = io.BytesIO()
        img2.save(img2_bytes, format='PNG')
        img2_data = img2_bytes.getvalue()

        prompt = """
        두 개의 NLS 검사 화면을 비교 분석해주세요.
        첫 번째 이미지는 이전 검사, 두 번째 이미지는 이후 검사입니다.

        다음 항목을 분석해주세요:
        1. 변화된 부분
        2. 개선된 영역
        3. 악화된 영역
        4. 전체적인 변화 트렌드
        5. 추가 권장 사항

        JSON 형식으로 반환해주세요.
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=img1_data, mime_type="image/png"),
                        types.Part.from_bytes(data=img2_data, mime_type="image/png"),
                    ]
                )
            ]
        )

        return {
            "comparison": response.text,
            "model": self.model_name,
            "timestamp": datetime.now().isoformat()
        }

    def extract_text_from_image(self, image_path: str) -> dict:
        """이미지에서 텍스트 추출 (OCR 대용)"""
        prompt = """
        이 이미지에서 보이는 모든 텍스트를 추출해주세요.
        텍스트의 위치와 내용을 함께 알려주세요.

        JSON 형식으로 반환:
        {
            "texts": [
                {"content": "텍스트 내용", "location": "위치 설명"},
                ...
            ]
        }
        """

        return self.analyze_image(image_path, prompt)


class AnalysisReport:
    """분석 결과 리포트 생성"""

    def __init__(self, save_dir: str = "./reports"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        analysis_results: list[dict],
        patient_info: Optional[dict] = None
    ) -> str:
        """분석 결과 리포트 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nls_report_{timestamp}.json"
        filepath = self.save_dir / filename

        report = {
            "generated_at": datetime.now().isoformat(),
            "patient_info": patient_info,
            "analysis_count": len(analysis_results),
            "results": analysis_results
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def generate_summary(self, analysis_results: list[dict]) -> str:
        """분석 결과 요약 생성"""
        summaries = []
        for i, result in enumerate(analysis_results, 1):
            analysis = result.get("analysis", "분석 결과 없음")
            summaries.append(f"=== 분석 {i} ===\n{analysis}\n")

        return "\n".join(summaries)
