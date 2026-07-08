"""git status / git diff 결과를 수집하는 유틸리티."""

import subprocess
import sys


class GitError(Exception):
    pass


def _run_git(args):
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except FileNotFoundError:
        raise GitError("git 명령을 찾을 수 없습니다. Git이 설치되어 있는지 확인하세요.")
    except subprocess.CalledProcessError as e:
        raise GitError(f"git {' '.join(args)} 실행 실패: {e.stderr.strip()}")


def is_git_repo() -> bool:
    try:
        _run_git(["rev-parse", "--is-inside-work-tree"])
        return True
    except GitError:
        return False


def get_git_status() -> str:
    """git status --porcelain 결과 (변경 파일 목록)."""
    return _run_git(["status", "--porcelain"])


def get_git_diff() -> str:
    """작업 트리(unstaged) + staged diff를 합쳐서 반환한다."""
    unstaged = _run_git(["diff"]) or ""       # ← None 방어
    staged = _run_git(["diff", "--cached"]) or ""  # ← None 방어
    combined = ""
    if staged.strip():
        combined += "### Staged changes\n" + staged
    if unstaged.strip():
        combined += "\n### Unstaged changes\n" + unstaged
    return combined


def has_changes() -> bool:
    status = get_git_status()
    return bool(status.strip())


def get_changed_files() -> list[str]:
    """git status --porcelain 출력에서 변경된 파일 경로만 추출."""
    status = get_git_status()
    files = []
    for line in status.splitlines():
        line = line.strip()
        if not line:
            continue
        # "M  path/to/file" 형태 -> 앞 2글자는 상태 코드
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            files.append(parts[1])
    return files


def ensure_git_repo():
    if not is_git_repo():
        print("[오류] 현재 디렉토리는 Git 저장소가 아닙니다. Git이 초기화된 프로젝트 루트에서 실행하세요.")
        sys.exit(1)
