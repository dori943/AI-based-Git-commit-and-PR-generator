#!/usr/bin/env python3
"""Gemini API 기반 Git 커밋 메시지 / PR 초안 생성 CLI.

사용 예:
    python cli.py commit
    python cli.py pr --model gemini-2.5-flash --temperature 0.2 --max-tokens 600
    python cli.py commit --safe-mode
"""

import argparse
import sys

import git_utils
import security
from ai_client import call_ai, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, AIClientError
from prompts import build_commit_prompt, build_pr_prompt, build_pr_retry_prompt
from formatter import validate_commit, validate_pr, format_commit_output, format_pr_output


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Git 변경 사항을 기반으로 AI가 커밋 메시지 / PR 초안을 생성합니다.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_options(p):
        p.add_argument("--model", default=DEFAULT_MODEL, help=f"사용할 모델 (기본값: {DEFAULT_MODEL})")
        p.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                        help=f"생성 다양성 조절 0.0~1.0 (기본값: {DEFAULT_TEMPERATURE})")
        p.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        help=f"최대 생성 토큰 수 (기본값: {DEFAULT_MAX_TOKENS})")
        p.add_argument("--safe-mode", action="store_true",
                        help="diff 전송 전 민감정보 마스킹 + 최대 10개 파일/200줄로 제한")

    commit_parser = subparsers.add_parser("commit", help="커밋 메시지 생성")
    add_common_options(commit_parser)

    pr_parser = subparsers.add_parser("pr", help="PR 제목/본문 생성")
    add_common_options(pr_parser)

    return parser


def collect_git_context(safe_mode: bool):
    git_utils.ensure_git_repo()

    if not git_utils.has_changes():
        print("변경 사항이 없습니다.")
        sys.exit(0)

    status_text = git_utils.get_git_status()
    diff_text = git_utils.get_git_diff()
    diff_text = security.apply_safe_mode(diff_text, safe_mode)

    return status_text, diff_text


def run_commit(args):
    status_text, diff_text = collect_git_context(args.safe_mode)
    prompt = build_commit_prompt(status_text, diff_text)

    print(f"[로그] AI API 호출 1회 시작 (model={args.model}, temperature={args.temperature}, max_tokens={args.max_tokens})")
    try:
        raw_text = call_ai(prompt, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
    except AIClientError as e:
        print(f"[오류] {e}")
        sys.exit(1)
    print("[로그] AI API 호출 완료 (총 1회)")

    validated = validate_commit(raw_text)
    print(format_commit_output(validated))


def run_pr(args):
    status_text, diff_text = collect_git_context(args.safe_mode)
    prompt = build_pr_prompt(status_text, diff_text)

    call_count = 0
    print(f"[로그] AI API 호출 시작 (model={args.model}, temperature={args.temperature}, max_tokens={args.max_tokens})")
    try:
        raw_text = call_ai(prompt, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
        call_count += 1
    except AIClientError as e:
        print(f"[오류] {e}")
        sys.exit(1)

    validated = validate_pr(raw_text)

    # Why/What/How to Test 중 하나라도 불릿이 없으면 1회 한정 재시도 (최대 2회 호출)
    if not validated["all_sections_ok"]:
        print("[로그] 일부 섹션이 비어 있어 강화된 프롬프트로 1회 재시도합니다...")
        retry_prompt = build_pr_retry_prompt(status_text, diff_text)
        try:
            raw_text_retry = call_ai(retry_prompt, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
            call_count += 1
            retry_validated = validate_pr(raw_text_retry)
            # 재시도 결과가 더 낫다면 교체
            if retry_validated["all_sections_ok"] or not validated["all_sections_ok"]:
                validated = retry_validated
        except AIClientError as e:
            print(f"[경고] 재시도 실패, 최초 결과로 진행합니다: {e}")

    print(f"[로그] AI API 호출 완료 (총 {call_count}회)")
    print(format_pr_output(validated))


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "commit":
        run_commit(args)
    elif args.command == "pr":
        run_pr(args)


if __name__ == "__main__":
    main()
