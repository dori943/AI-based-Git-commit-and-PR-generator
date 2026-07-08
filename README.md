# AI Git Commit/PR Assistant (Gemini API 버전)

Git 변경 사항(`git status`, `git diff`)을 읽어 Google Gemini API를 호출하고,
커밋 메시지와 Pull Request 초안을 자동으로 생성해주는 CLI 도구입니다.

## 1. 설치

```bash
git clone <your-repo-url>
cd ai-git-assistant
pip install -r requirements.txt
```

## 2. 환경변수(API Key) 설정

API Key는 **절대 코드에 하드코딩하지 않고** 환경변수로만 설정합니다.

```bash
# macOS / Linux
export GEMINI_API_KEY="your_api_key_here"

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"
```

API Key는 [Google AI Studio](https://aistudio.google.com/apikey)에서 발급받을 수 있습니다.

## 3. 실행 방법

**반드시 Git이 초기화된 프로젝트 루트 디렉토리에서 실행**해야 합니다.

### 커밋 메시지 생성

```bash
python cli.py commit
```

### PR 제목/본문 생성

```bash
python cli.py pr
```

### 옵션 (모델/temperature/max-tokens/safe-mode)

```bash
python cli.py commit --model gemini-2.5-flash --temperature 0.2 --max-tokens 600
python cli.py pr --safe-mode
```

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--model` | 사용할 Gemini 모델 | `gemini-2.5-flash` |
| `--temperature` | 생성 다양성(0.0~1.0, 낮을수록 일관적) | `0.3` |
| `--max-tokens` | 최대 생성 토큰 수 | `800` |
| `--safe-mode` | diff 전송 전 민감정보 마스킹 + 파일 10개/200줄로 제한 | 꺼짐 |

> 실제 사용 가능한 최신 모델 ID는 [Gemini API 공식 문서](https://ai.google.dev/gemini-api/docs/models)에서 확인하세요.
> (예: `gemini-2.5-flash`, `gemini-2.5-pro` 등)

## 4. 출력 예시

### `commit` 실행 결과 예시

```
[로그] AI API 호출 1회 시작 (model=gemini-2.5-flash, temperature=0.3, max_tokens=800)
[로그] AI API 호출 완료 (총 1회)
============================================================
커밋 메시지 (Commit Message)
============================================================
[제목] fix: null 체크 누락으로 인한 로그인 API 500 오류 수정
------------------------------------------------------------
[본문]
- auth/login.py: 사용자 조회 결과가 None일 때 예외 대신 400 응답 반환하도록 수정
- 관련 유닛 테스트 1건 추가
============================================================
```

### `pr` 실행 결과 예시

```
============================================================
Pull Request 초안
============================================================
[PR 제목] fix: 로그인 API 500 오류 수정 및 null 체크 보강
------------------------------------------------------------
## Why ✔
- 사용자 조회 실패 시 서버가 500 오류를 반환하는 버그가 보고됨

## What ✔
- auth/login.py에 null 체크 로직 추가
- 실패 시 400 상태코드와 에러 메시지 반환

## How to Test ✔
- pytest tests/test_login.py 실행하여 신규 테스트 통과 확인
============================================================
```

## 5. 주의사항 (운영 관점)

- **민감정보**: `git diff`에는 API Key, 개인정보, 비밀번호 등이 포함될 수 있습니다.
  `--safe-mode` 옵션을 사용하면 diff 전송 전 다음을 자동 적용합니다.
  - API Key/토큰/이메일/비밀번호로 추정되는 패턴 마스킹
  - 최대 10개 파일, 200줄까지만 diff 전송 (그 이상은 생략 표시)
  - 단, 패턴 기반 마스킹은 완벽하지 않으므로 민감한 저장소에서는 결과를 반드시 재검토하세요.
- **비용/요청 횟수 제한**: `commit`, `pr` 명령은 각각 Gemini API를 **1회만 호출**하며,
  실행 시 터미널에 호출 로그(`[로그] AI API 호출 ...`)가 출력됩니다.
  Gemini API는 무료 등급에도 분당/일일 요청 한도가 있으니 반복 실행 시 429 오류에 유의하세요.
- 생성된 커밋/PR 텍스트는 **초안**입니다. 최종 적용 전 반드시 사람이 검토하세요.
- 이 도구는 `git push`나 GitHub PR 자동 생성(API 연동)은 수행하지 않습니다.
  생성된 텍스트를 복사해 직접 커밋/PR을 작성하는 흐름을 전제로 합니다.

## 6. 참고: Gemini API 호출 구조

이 프로젝트는 REST API를 `requests`로 직접 호출합니다 (`ai_client.py`).

```
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=API_KEY
{
  "contents": [{"role": "user", "parts": [{"text": "..."}]}],
  "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800}
}
```

공식 SDK(`google-genai`)를 사용하고 싶다면 `requirements.txt`의 주석을 해제하고
`ai_client.py`의 요청 부분만 SDK 호출로 교체하면 됩니다.
