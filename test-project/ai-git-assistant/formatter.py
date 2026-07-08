"""생성된 커밋/PR 텍스트의 길이·형식 규칙 검증 및 후처리."""

import re

COMMIT_TITLE_MAX = 72
PR_TITLE_MAX = 80
REQUIRED_PR_SECTIONS = ["Why", "What", "How to Test"]


def split_commit_message(text: str):
    lines = text.strip().splitlines()
    title = lines[0].strip() if lines else ""
    body = "\n".join(lines[1:]).strip()
    return title, body


def enforce_commit_title_length(title: str) -> str:
    """제목이 규칙(최대 72자)을 넘으면 잘라낸다(후처리 방식)."""
    if len(title) > COMMIT_TITLE_MAX:
        return title[: COMMIT_TITLE_MAX - 3].rstrip() + "..."
    return title


def validate_commit(text: str) -> dict:
    title, body = split_commit_message(text)
    title = enforce_commit_title_length(title)

    has_file_mention = bool(re.search(r"[\w./-]+\.\w+", body))  # 파일명 패턴 대략 탐지
    has_bullet = bool(re.search(r"^\s*[-*]\s+", body, flags=re.MULTILINE))

    return {
        "title": title,
        "body": body,
        "title_ok": len(title) <= COMMIT_TITLE_MAX,
        "body_meets_min_quality": has_file_mention or has_bullet,
    }


def parse_pr_draft(text: str):
    """Title / Why / What / How to Test 섹션 파싱."""
    title_match = re.search(r"Title:\s*(.+)", text)
    title = title_match.group(1).strip() if title_match else ""

    sections = {}
    for i, name in enumerate(REQUIRED_PR_SECTIONS):
        pattern = rf"##\s*{re.escape(name)}\s*\n(.*?)(?=\n##\s*|\Z)"
        m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        sections[name] = m.group(1).strip() if m else ""

    return title, sections


def enforce_pr_title_length(title: str) -> str:
    if len(title) > PR_TITLE_MAX:
        return title[: PR_TITLE_MAX - 3].rstrip() + "..."
    return title


def validate_pr(text: str) -> dict:
    title, sections = parse_pr_draft(text)
    title = enforce_pr_title_length(title)

    section_status = {}
    for name, content in sections.items():
        bullets = re.findall(r"^\s*[-*]\s+.+", content, flags=re.MULTILINE)
        section_status[name] = {
            "present": bool(content.strip()),
            "bullet_count": len(bullets),
            "ok": len(bullets) >= 1,
        }

    return {
        "title": title,
        "sections": sections,
        "section_status": section_status,
        "title_ok": len(title) <= PR_TITLE_MAX,
        "all_sections_ok": all(s["ok"] for s in section_status.values()),
    }


def format_commit_output(validated: dict) -> str:
    lines = [
        "=" * 60,
        "커밋 메시지 (Commit Message)",
        "=" * 60,
        f"[제목] {validated['title']}",
    ]
    if validated["body"]:
        lines.append("-" * 60)
        lines.append("[본문]")
        lines.append(validated["body"])
    lines.append("=" * 60)
    if not validated["title_ok"]:
        lines.append("⚠ 제목이 72자를 초과하여 잘렸습니다.")
    if not validated["body_meets_min_quality"]:
        lines.append("⚠ 본문에 파일 언급/불릿 요약이 부족할 수 있습니다. 검토를 권장합니다.")
    return "\n".join(lines)


def format_pr_output(validated: dict) -> str:
    lines = [
        "=" * 60,
        "Pull Request 초안",
        "=" * 60,
        f"[PR 제목] {validated['title']}",
        "-" * 60,
    ]
    for name in REQUIRED_PR_SECTIONS:
        status = validated["section_status"][name]
        marker = "✔" if status["ok"] else "⚠"
        lines.append(f"## {name} {marker}")
        lines.append(validated["sections"][name] or "(내용 없음)")
        lines.append("")
    lines.append("=" * 60)
    if not validated["title_ok"]:
        lines.append("⚠ PR 제목이 80자를 초과하여 잘렸습니다.")
    if not validated["all_sections_ok"]:
        lines.append("⚠ 일부 섹션에 불릿이 없습니다. 내용을 보완하세요.")
    return "\n".join(lines)
