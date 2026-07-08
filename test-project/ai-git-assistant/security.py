"""safe-mode: 민감정보 마스킹 + diff 크기 제한."""

import re

# 자주 쓰이는 API Key / 토큰 패턴 (형태 기반 탐지, 완벽하지 않음 - 참고용)
SENSITIVE_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{16,}"), "sk-****MASKED****"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA****MASKED****"),
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)['\"]?[A-Za-z0-9_\-]{12,}['\"]?"), r"\1****MASKED****"),
    (re.compile(r"(?i)(secret\s*[:=]\s*)['\"]?[A-Za-z0-9_\-]{8,}['\"]?"), r"\1****MASKED****"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "****EMAIL_MASKED****"),
    (re.compile(r"(?i)(password\s*[:=]\s*)['\"]?\S+['\"]?"), r"\1****MASKED****"),
]

MAX_FILES = 10
MAX_LINES = 200


def mask_sensitive(text: str) -> str:
    """diff 텍스트에서 민감해 보이는 패턴을 마스킹한다."""
    masked = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


def truncate_diff(text: str, max_files: int = MAX_FILES, max_lines: int = MAX_LINES) -> str:
    """diff를 최대 파일 수 / 최대 줄 수로 제한한다."""
    lines = text.splitlines()

    # 파일 단위 블록 개수 제한 (diff --git 로 시작하는 블록 기준)
    file_count = 0
    kept_lines = []
    for line in lines:
        if line.startswith("diff --git"):
            file_count += 1
            if file_count > max_files:
                kept_lines.append(f"\n...(이후 {max_files}개 초과 파일 생략됨)...")
                break
        kept_lines.append(line)

    # 줄 수 제한
    if len(kept_lines) > max_lines:
        kept_lines = kept_lines[:max_lines] + [f"...(이후 {max_lines}줄 초과분 생략됨)..."]

    return "\n".join(kept_lines)


def apply_safe_mode(diff_text: str, safe_mode: bool) -> str:
    """safe-mode가 켜져 있으면 마스킹 + 크기 제한을 모두 적용한다."""
    if not safe_mode:
        return diff_text
    masked = mask_sensitive(diff_text)
    truncated = truncate_diff(masked)
    return truncated
