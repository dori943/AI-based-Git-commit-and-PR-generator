"""Google Gemini API(REST) 호출 래퍼.

- API Key는 환경변수 GEMINI_API_KEY 에서만 읽는다 (하드코딩 금지).
- 모델/온도/최대토큰은 호출부(CLI)에서 파라미터로 넘어온다.
"""

import os
import requests

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# 실제 사용 가능한 최신 모델 ID는 https://ai.google.dev/gemini-api/docs/models 에서 확인하세요.
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 800


class AIClientError(Exception):
    pass


def call_ai(prompt: str, model: str = DEFAULT_MODEL,
            temperature: float = DEFAULT_TEMPERATURE,
            max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """Gemini API를 1회 호출하고 텍스트 응답을 반환한다."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise AIClientError(
            "GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다. "
            "export GEMINI_API_KEY=your_key 로 설정 후 다시 시도하세요."
        )

    url = f"{API_BASE}/{model}:generateContent"
    headers = {"content-type": "application/json"}
    params = {"key": api_key}
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            # gemini-2.5 계열은 기본적으로 답변 전에 내부 추론(thinking)에
            # 토큰을 먼저 소비한다. 이 예산도 max_tokens 안에서 차감되므로,
            # thinking을 꺼서 모든 토큰이 실제 출력에 쓰이도록 한다.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=body, timeout=30)
    except requests.exceptions.ConnectionError:
        raise AIClientError("네트워크 오류: API 서버에 연결할 수 없습니다. 인터넷 연결을 확인하세요.")
    except requests.exceptions.Timeout:
        raise AIClientError("요청 시간 초과: API 응답이 너무 늦습니다. 잠시 후 다시 시도하세요.")

    if response.status_code == 400:
        raise AIClientError(f"잘못된 요청(400): {response.text[:300]}")
    if response.status_code in (401, 403):
        raise AIClientError("인증 실패: API Key가 올바른지, 활성화되어 있는지 확인하세요.")
    if response.status_code == 429:
        raise AIClientError("요청 한도 초과(429): 잠시 후 다시 시도하세요.")
    if response.status_code >= 400:
        raise AIClientError(f"API 오류({response.status_code}): {response.text[:300]}")

    data = response.json()

    try:
        candidates = data.get("candidates", [])
        if not candidates:
            # 안전 필터 등으로 응답이 차단된 경우 promptFeedback에 사유가 담김
            feedback = data.get("promptFeedback", {})
            raise AIClientError(f"API 응답에 결과가 없습니다. 사유: {feedback}")

        finish_reason = candidates[0].get("finishReason", "")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise AIClientError(f"API 응답에서 텍스트를 찾을 수 없습니다. (finishReason={finish_reason})")
        if finish_reason == "MAX_TOKENS":
            text += f"\n\n[경고] 응답이 max_tokens({max_tokens}) 제한으로 중간에 잘렸습니다. --max-tokens 값을 늘려보세요."
        return text
    except (KeyError, IndexError) as e:
        raise AIClientError(f"API 응답 파싱 실패: {e}")