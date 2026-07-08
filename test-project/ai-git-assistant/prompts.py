"""커밋 메시지 / PR 초안 생성을 위한 프롬프트 템플릿.

설계 원칙:
- 각 불릿/문장은 짧게(15단어 내외) 제한해, 앞부분(Why)에서 장황해져
  뒷부분(What/How to Test)이 max_tokens 안에 못 들어가는 문제를 방지한다.
- 불릿 개수 자체를 상한선(예: 2~3개)으로 못박아 "요약"에 집중시킨다.
- 서론/결론/부연설명 문장을 명시적으로 금지해, 형식 밖의 텍스트가
  토큰을 잡아먹지 않도록 한다.
"""


def build_commit_prompt(status_text: str, diff_text: str) -> str:
    return f"""당신은 숙련된 소프트웨어 엔지니어의 커밋 메시지 작성을 돕는 도우미입니다.
아래 Git 변경 사항을 바탕으로 커밋 메시지를 작성하세요.

[분량 제한 - 반드시 지킬 것]
- 전체 출력은 5줄을 넘기지 마세요.
- 모든 문장/불릿은 1줄, 15단어 이내로 짧게 쓰세요.
- 서론, 결론, 부연설명, 감상 문장은 절대 쓰지 마세요. 형식 그대로만 출력하세요.

[출력 형식 - 이 형식만 그대로 출력]
<커밋 제목 1줄, 50자 이내 권장, 최대 72자, 명령형>

- <변경된 파일/모듈 1개 + 핵심 변경 내용, 한 줄>
- <핵심 변경 내용 추가 1개, 한 줄> (선택, 없으면 생략)

[git status]
{status_text.strip() or "(없음)"}

[git diff]
{diff_text.strip() or "(없음)"}
"""


def build_pr_prompt(status_text: str, diff_text: str) -> str:
    return f"""당신은 Pull Request 초안 작성을 돕는 도우미입니다.
아래 Git 변경 사항을 바탕으로 PR 제목과 본문을 작성하세요.

[분량 제한 - 반드시 지킬 것]
- 전체 출력은 12줄을 넘기지 마세요.
- 각 섹션의 불릿은 최대 2개, 각 불릿은 1줄·15단어 이내로 짧게.
- Why/What/How to Test 세 섹션 모두 반드시 채우세요. 어느 하나도 비워두지 마세요.
- 서론, 결론, 요약, 감상, 부연설명 문장은 절대 쓰지 마세요.
- 아래 형식 외의 텍스트(설명, 코드블록, 따옴표)는 절대 출력하지 마세요.

[출력 형식 - 이 형식만 그대로 출력]
Title: <PR 제목, 최대 80자, 1줄>

## Why
- <변경 배경, 한 줄>

## What
- <핵심 변경 사항, 한 줄>

## How to Test
- <테스트 방법, 한 줄>

[git status]
{status_text.strip() or "(없음)"}

[git diff]
{diff_text.strip() or "(없음)"}
"""


def build_pr_retry_prompt(status_text: str, diff_text: str) -> str:
    """Why/What/How to Test 중 일부가 비어 있을 때 재시도용으로 더 엄격하게 지시하는 프롬프트."""
    base = build_pr_prompt(status_text, diff_text)
    return base + """
[중요 - 이전 시도에서 일부 섹션이 비어 있었거나 응답이 중간에 끊겼습니다]
반드시 아래 순서를 지키세요:
1. 먼저 Why, What, How to Test 세 섹션에 넣을 한 줄짜리 불릿을 각각 미리 생각하세요.
2. Why를 길게 쓰지 말고 딱 1줄로 끝내고 바로 What으로 넘어가세요.
3. diff에서 구체적 정보를 찾기 어렵다면 git status의 파일명만으로도 좋으니
   절대 섹션을 비우지 말고 짧게라도 채우세요.
4. What과 How to Test까지 반드시 출력을 끝맺으세요. Why에서 절대 멈추지 마세요.
"""