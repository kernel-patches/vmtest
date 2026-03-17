#!/usr/bin/env python3
"""Stagger CI runs during KPD rebase storms.

When KPD rebases all PR branches after an upstream commit, hundreds of
workflow runs fire at once.  This script detects the storm and waits for
it to subside before letting the expensive build jobs start.

Storm = all of:
  1. PR synchronize event (force-push rebase, not a new PR)
  2. Base branch updated within the last 30 minutes (KPD just mirrored)
  3. Active workflow runs (queued + in-progress) >= half of open PRs

Re-checks in a loop with random 1-15 min sleeps.  Gives up after 2 hours.
cancel-in-progress on the concurrency group kills sleeping runs on new pushes.
"""

import os
import random
import time
from datetime import datetime, timezone

import requests

BASE_BRANCH_RECENCY_S = 1800  # base branch "just updated" threshold
STORM_RATIO = 0.5  # active runs / open PRs threshold
WAIT_MIN_S = 60  # min sleep per iteration
WAIT_MAX_S = 900  # max sleep per iteration
MAX_TOTAL_WAIT_S = 7200  # hard cap on total wait


def gh_api(endpoint):
    token = os.environ.get("GITHUB_TOKEN", "")
    resp = requests.get(
        f"https://api.github.com{endpoint}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    resp.raise_for_status()
    return resp.json()


def base_branch_age_s(repo, base_branch):
    """Seconds since last commit on the base branch, or None on error."""
    try:
        sha = gh_api(f"/repos/{repo}/branches/{base_branch}")["commit"]["sha"]
        date_str = gh_api(f"/repos/{repo}/commits/{sha}")["commit"]["committer"]["date"]
        commit_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - commit_time).total_seconds()
    except Exception as e:
        print(f"Warning: could not get base branch age: {e}")
        return None


def active_run_count(repo):
    """Number of queued + in-progress workflow runs."""
    total = 0
    for status in ("queued", "in_progress"):
        try:
            data = gh_api(f"/repos/{repo}/actions/runs?status={status}&per_page=1")
            total += data.get("total_count", 0)
        except Exception as e:
            print(f"Warning: could not query {status} runs: {e}")
    return total


def open_pr_count(repo):
    """Number of open pull requests."""
    try:
        data = gh_api(f"/search/issues?q=repo:{repo}+type:pr+state:open&per_page=1")
        return data.get("total_count", 0)
    except Exception as e:
        print(f"Warning: could not query open PRs: {e}")
        return 0


def is_storm(repo, base_branch):
    age = base_branch_age_s(repo, base_branch)
    if age is None or age > BASE_BRANCH_RECENCY_S:
        print(f"Base branch {base_branch} updated {age}s ago — no storm.")
        return False

    active = active_run_count(repo)
    open_prs = open_pr_count(repo)
    if open_prs == 0:
        return False

    ratio = active / open_prs
    if ratio < STORM_RATIO:
        print(f"{active} active / {open_prs} PRs ({ratio:.0%}) — no storm.")
        return False

    print(
        f"Storm: base {base_branch} updated {age:.0f}s ago, "
        f"{active} active / {open_prs} PRs ({ratio:.0%})."
    )
    return True


def main():
    action = os.environ.get("GITHUB_EVENT_ACTION", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    base = os.environ.get("PR_BASE_BRANCH", "")

    if action != "synchronize":
        return

    if not repo or not base:
        return

    start = time.monotonic()
    while is_storm(repo, base):
        elapsed = time.monotonic() - start
        remaining = MAX_TOTAL_WAIT_S - elapsed
        if remaining <= 0:
            print(f"Hit {MAX_TOTAL_WAIT_S}s cap — proceeding.")
            break
        delay = random.randint(WAIT_MIN_S, min(WAIT_MAX_S, int(remaining)))
        print(f"Waiting {delay}s (elapsed: {elapsed:.0f}s)...")
        time.sleep(delay)


if __name__ == "__main__":
    main()
