"""커밋 메시지 / PR 초안 생성을 위한 프롬프트 템플릿."""


def build_commit_prompt(status_text: str, diff_text: str) -> str:
    return f"""당신은 숙련된 소프트웨어 엔지니어의 커밋 메시지 작성을 돕는 도우미입니다.
아래 Git 변경 사항을 바탕으로 커밋 메시지를 작성하세요.

[규칙]
- 첫 줄: 커밋 제목 (50자 이내 권장, 최대 72자). 명령형으로 간결하게.
- 그 다음 빈 줄 후 본문(선택): 변경된 파일/모듈 1~3개 언급 + 핵심 변경사항을 불릿(-)으로 1~2개 요약.
- 불필요한 수식어나 장황한 설명 없이 사실 기반으로 작성.
- 출력은 커밋 메시지 텍스트만. 다른 설명/따옴표/마크다운 코드블록 금지.

[git status]
{status_text.strip() or "(없음)"}

[git diff]
{diff_text.strip() or "(없음)"}
"""


def build_pr_prompt(status_text: str, diff_text: str) -> str:
    return f"""당신은 Pull Request 초안 작성을 돕는 도우미입니다.
아래 Git 변경 사항을 바탕으로 PR 제목과 본문을 작성하세요.

[출력 형식 - 반드시 그대로 따를 것]
Title: <PR 제목, 최대 80자, 1줄>

## Why
- <변경 배경 불릿 최소 1개>

## What
- <핵심 변경 사항 불릿 최소 1개>

## How to Test
- <테스트 방법 불릿 최소 1개>

[규칙]
- 각 섹션에는 최소 1개 이상의 불릿(-)을 포함할 것.
- 다른 설명이나 마크다운 코드블록 없이 위 형식만 출력.

[git status]
{status_text.strip() or "(없음)"}

[git diff]
{diff_text.strip() or "(없음)"}
"""


def build_pr_retry_prompt(status_text: str, diff_text: str) -> str:
    """Why/What/How to Test 중 일부가 비어 있을 때 재시도용으로 더 엄격하게 지시하는 프롬프트."""
    base = build_pr_prompt(status_text, diff_text)
    return base + """
[중요 - 이전 시도에서 일부 섹션이 비어 있었습니다]
Why, What, How to Test 세 섹션 모두 절대 비워두지 마세요.
diff에서 실제 정보를 찾을 수 없더라도, git status에 나온 변경 파일명을 근거로
최소 1개의 불릿을 반드시 채워 넣으세요. 섹션을 생략하거나 빈 채로 두는 것은 허용되지 않습니다.
"""

