#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional


GITHUB_API = os.environ.get("GITHUB_API", "https://api.github.com").rstrip("/")

TOKEN_ENV_CANDIDATES = ("GITHUB_TOKEN", "GH_TOKEN")


DEFAULT_REQUIRED_CHECKS = [
    "swarm/state-guard",
    "swarm/policy-guard",
    "quality/no-mocks",
    "quality/no-placeholders",
    "tests/unit-integration",
    "tests/e2e",
    "attest/ci-summary",
]


@dataclass(frozen=True)
class Repo:
    owner: str
    name: str


class GhError(RuntimeError):
    pass


def _get_token() -> str:
    for k in TOKEN_ENV_CANDIDATES:
        v = os.environ.get(k)
        if v:
            return v
    raise GhError(
        "Missing GitHub token. Set GITHUB_TOKEN (recommended) or GH_TOKEN in the environment."
    )


def _run_git(args: list[str]) -> str:
    res = subprocess.run(["git", *args], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise GhError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout.strip()


def _detect_repo_from_env() -> Optional[Repo]:
    repo = (os.environ.get("GITHUB_REPO") or "").strip()
    if repo and "/" in repo:
        owner, name = repo.split("/", 1)
        if owner and name:
            return Repo(owner=owner, name=name)

    owner = (os.environ.get("GITHUB_OWNER") or "").strip()
    name = (os.environ.get("GITHUB_REPO_NAME") or os.environ.get("GITHUB_REPO") or "").strip()
    if owner and name and "/" not in name:
        return Repo(owner=owner, name=name)
    return None


def _detect_repo_from_git_remote() -> Repo:
    url = _run_git(["remote", "get-url", "origin"])

    # Normalize common forms:
    # - https://github.com/OWNER/REPO.git
    # - https://<token>@github.com/OWNER/REPO.git
    # - git@github.com:OWNER/REPO.git
    https = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if https:
        return Repo(owner=https.group(1), name=https.group(2))

    ssh = re.search(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if ssh:
        return Repo(owner=ssh.group(1), name=ssh.group(2))

    raise GhError(
        "Unable to detect GitHub repo from environment or git remote. "
        "Set GITHUB_REPO=owner/repo or ensure `git remote get-url origin` is a github.com URL."
    )


def _detect_repo() -> Repo:
    env_repo = _detect_repo_from_env()
    if env_repo:
        return env_repo
    return _detect_repo_from_git_remote()


def _api_request(
    *,
    token: str,
    method: str,
    path: str,
    query: Optional[dict[str, str]] = None,
    body: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    url = f"{GITHUB_API}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "cmas-os-gh-pr-gate",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise GhError(f"GitHub API {method} {path} failed: HTTP {e.code}: {msg[:500]}") from e
    except urllib.error.URLError as e:
        raise GhError(f"GitHub API {method} {path} failed: {e}") from e

    if not raw.strip():
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise GhError(f"GitHub API returned non-JSON for {method} {path}: {raw[:200]}") from e

    if not isinstance(data, dict):
        # Some endpoints can return arrays, but we only call dict-returning ones here.
        raise GhError(f"GitHub API returned unexpected JSON type for {method} {path}: {type(data).__name__}")
    return data


def _get_required_checks(token: str, repo: Repo, branch: str) -> list[str]:
    # Use branch protection as the authoritative list of required checks.
    try:
        data = _api_request(
            token=token,
            method="GET",
            path=f"/repos/{repo.owner}/{repo.name}/branches/{branch}/protection",
        )
        rsc = data.get("required_status_checks") or {}
        contexts = rsc.get("contexts")
        if isinstance(contexts, list) and all(isinstance(x, str) for x in contexts) and contexts:
            return list(contexts)
    except GhError:
        # Fall back to defaults if branch protection is unavailable.
        pass

    return list(DEFAULT_REQUIRED_CHECKS)


def _get_pr(token: str, repo: Repo, pr_number: int) -> dict[str, Any]:
    return _api_request(
        token=token,
        method="GET",
        path=f"/repos/{repo.owner}/{repo.name}/pulls/{pr_number}",
    )


def _list_open_prs(token: str, repo: Repo, base: str) -> list[dict[str, Any]]:
    # REST returns array; use urllib directly to keep API helper dict-only.
    url = f"{GITHUB_API}/repos/{repo.owner}/{repo.name}/pulls?{urllib.parse.urlencode({'state':'open','base':base,'sort':'updated','direction':'desc','per_page':'20'})}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "cmas-os-gh-pr-gate",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if not isinstance(data, list):
        raise GhError("Unexpected response type listing pull requests.")
    return [x for x in data if isinstance(x, dict)]


def _get_check_runs(token: str, repo: Repo, sha: str) -> dict[str, dict[str, Any]]:
    data = _api_request(
        token=token,
        method="GET",
        path=f"/repos/{repo.owner}/{repo.name}/commits/{sha}/check-runs",
        query={"per_page": "100"},
    )
    runs = data.get("check_runs") or []
    if not isinstance(runs, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for r in runs:
        if not isinstance(r, dict):
            continue
        name = r.get("name")
        if isinstance(name, str) and name:
            out[name] = r
    return out


def _summarize_required_checks(
    required: list[str],
    runs_by_name: dict[str, dict[str, Any]],
) -> tuple[bool, bool, list[str], list[str]]:
    """
    Returns:
      (all_present, all_completed, ok_names, bad_lines)
    """
    all_present = True
    all_completed = True
    ok: list[str] = []
    bad: list[str] = []

    for name in required:
        run = runs_by_name.get(name)
        if not run:
            all_present = False
            all_completed = False
            bad.append(f"{name}: MISSING")
            continue
        status = run.get("status")
        conclusion = run.get("conclusion")
        details = run.get("html_url") or run.get("details_url") or ""
        if status != "completed":
            all_completed = False
            bad.append(f"{name}: status={status} conclusion={conclusion} {details}".rstrip())
            continue
        if conclusion == "success":
            ok.append(name)
            continue
        bad.append(f"{name}: status=completed conclusion={conclusion} {details}".rstrip())

    return all_present, all_completed, ok, bad


def _get_self_login(token: str) -> str:
    data = _api_request(token=token, method="GET", path="/user")
    login = data.get("login")
    if not isinstance(login, str) or not login:
        raise GhError("Unable to determine token user login via /user.")
    return login


def _already_approved_by_self(token: str, repo: Repo, pr_number: int, self_login: str) -> bool:
    url = f"{GITHUB_API}/repos/{repo.owner}/{repo.name}/pulls/{pr_number}/reviews?per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "cmas-os-gh-pr-gate",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if not isinstance(data, list):
        return False
    # Only the latest review state from the user matters; iterate from newest.
    for r in reversed(data):
        if not isinstance(r, dict):
            continue
        user = r.get("user")
        if not isinstance(user, dict):
            continue
        login = user.get("login")
        if login != self_login:
            continue
        state = r.get("state")
        if state == "APPROVED":
            return True
        # If user last left CHANGES_REQUESTED or COMMENTED, treat as not approved.
        return False
    return False


def _approve_pr(token: str, repo: Repo, pr_number: int, body: str) -> None:
    _api_request(
        token=token,
        method="POST",
        path=f"/repos/{repo.owner}/{repo.name}/pulls/{pr_number}/reviews",
        body={"event": "APPROVE", "body": body},
    )


def _merge_pr(token: str, repo: Repo, pr_number: int, *, method: str, title: str, message: str) -> None:
    _api_request(
        token=token,
        method="PUT",
        path=f"/repos/{repo.owner}/{repo.name}/pulls/{pr_number}/merge",
        body={"merge_method": method, "commit_title": title, "commit_message": message},
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "L2 gate for PRs: wait for required GitHub Actions checks to complete and succeed.\n"
            "Optionally APPROVE and MERGE the PR once it is green.\n"
            "\n"
            "This is intended to be the OpenClaw/Danny 'hard lock' in L2 mode:\n"
            "do not proceed to the next phase until this returns success and the PR is merged."
        )
    )
    parser.add_argument("--pr", type=int, default=0, help="PR number to gate. If omitted, uses the newest open PR against --base.")
    parser.add_argument("--base", default=os.environ.get("GITHUB_BRANCH", "main"), help="Base branch (default: main)")
    parser.add_argument("--timeout-seconds", type=int, default=1800, help="Timeout waiting for checks (default: 1800)")
    parser.add_argument("--poll-seconds", type=int, default=10, help="Polling interval (default: 10)")
    parser.add_argument("--approve", action="store_true", help="Post an APPROVE review when checks are green.")
    parser.add_argument("--merge", action="store_true", help="Merge the PR when checks are green (requires approvals if protected).")
    parser.add_argument("--merge-method", default="squash", choices=["merge", "squash", "rebase"], help="Merge method (default: squash)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args(argv)

    try:
        token = _get_token()
        repo = _detect_repo()
        base = args.base

        pr_number = args.pr
        if pr_number <= 0:
            prs = _list_open_prs(token, repo, base=base)
            if not prs:
                raise GhError(f"No open PRs found targeting base={base}.")
            pr_number = int(prs[0].get("number") or 0)
            if pr_number <= 0:
                raise GhError("Unable to infer PR number from GitHub API response.")

        required = _get_required_checks(token, repo, branch=base)

        start = time.time()
        last_sha = ""
        while True:
            pr = _get_pr(token, repo, pr_number)
            if pr.get("state") != "open":
                raise GhError(f"PR #{pr_number} is not open (state={pr.get('state')!r}).")

            head = pr.get("head") or {}
            head_sha = head.get("sha") if isinstance(head, dict) else None
            if not isinstance(head_sha, str) or not head_sha:
                raise GhError(f"Unable to read head SHA for PR #{pr_number}.")

            if head_sha != last_sha:
                last_sha = head_sha
                # Reset timer on new pushes: we need fresh results for the new SHA.
                start = time.time()

            runs = _get_check_runs(token, repo, head_sha)
            all_present, all_completed, ok_names, bad_lines = _summarize_required_checks(required, runs)

            if all_present and all_completed and not bad_lines:
                # Green.
                did_approve = False
                did_merge = False

                if args.approve:
                    self_login = _get_self_login(token)
                    if not _already_approved_by_self(token, repo, pr_number, self_login):
                        _approve_pr(
                            token,
                            repo,
                            pr_number,
                            body="CMAS-OS: CI required checks are green. Approved by orchestrator (Analyst gate).",
                        )
                        did_approve = True

                if args.merge:
                    title = f"Merge PR #{pr_number} (CMAS-OS)"
                    message = f"Merged by CMAS-OS orchestrator after required checks passed. PR: #{pr_number}"
                    _merge_pr(token, repo, pr_number, method=args.merge_method, title=title, message=message)
                    did_merge = True

                if args.json:
                    sys.stdout.write(
                        json.dumps(
                            {
                                "ok": True,
                                "repo": f"{repo.owner}/{repo.name}",
                                "pr": pr_number,
                                "head_sha": head_sha,
                                "required_checks": required,
                                "approved": did_approve,
                                "merged": did_merge,
                            },
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n"
                    )
                else:
                    sys.stdout.write(f"OK: PR #{pr_number} is GREEN for required checks.\n")
                    if did_approve:
                        sys.stdout.write("OK: PR approved.\n")
                    if did_merge:
                        sys.stdout.write("OK: PR merged.\n")
                return 0

            # If any required check completed with non-success, fail fast.
            any_failed = any("conclusion=" in ln and "conclusion=success" not in ln and "status=completed" in ln for ln in bad_lines)
            if any_failed:
                msg = {
                    "ok": False,
                    "repo": f"{repo.owner}/{repo.name}",
                    "pr": pr_number,
                    "head_sha": head_sha,
                    "required_checks": required,
                    "failures": bad_lines,
                }
                if args.json:
                    sys.stdout.write(json.dumps(msg, indent=2, sort_keys=True) + "\n")
                else:
                    sys.stderr.write(f"ERROR: PR #{pr_number} has failing required checks.\n")
                    for ln in bad_lines:
                        sys.stderr.write(f"- {ln}\n")
                return 1

            # Still running / missing checks.
            if time.time() - start > args.timeout_seconds:
                raise GhError(f"Timeout waiting for required checks on PR #{pr_number} (sha={head_sha}).")

            if not args.json:
                sys.stdout.write(f"WAIT: PR #{pr_number} sha={head_sha} waiting for required checks...\n")
                for ln in bad_lines:
                    sys.stdout.write(f"- {ln}\n")
            time.sleep(args.poll_seconds)

    except GhError as e:
        if args.json:
            sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, indent=2, sort_keys=True) + "\n")
        else:
            sys.stderr.write(f"ERROR: {e}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
