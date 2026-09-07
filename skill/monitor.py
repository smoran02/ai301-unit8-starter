#!/usr/bin/env python3
"""pr-monitor: your contribution's state, read on demand, with the
next move drafted. The toolkit's capstone: a tool that runs with no
session open.

Units 5-7 built tools that live inside an interactive session: skills
you invoke (the scout), hooks that latch the session's doorways (the
voice-guard, the ship-gate). The monitor is different in kind: one
program, run from the shell, that gathers your pull request's live
state through READ-ONLY gh calls (checks, review threads and comments
new since your last run, days of quiet, mergeability, merged or
closed, or the honest no-PR-yet), classifies the state, folds in YOUR
playbook and the matching move form, makes ONE print-mode model call,
and writes two files: the run report (the state, honestly) and the
drafted move. Staff wrote the state reading and the move forms; the
judgment, the thresholds, the rules, and every word that finally
reaches a maintainer are yours.

Two ways to run it, both from inside your clone, on your branch:

  full run (no arguments): gather the state, classify it, and draft
    the matching move: a never-defensive review response, a rebase
    plan, a polite nudge (only if your own playbook's threshold says
    so), or a merged follow-up. The report and the draft land in
    this folder; every run appends a dated block to monitor-log.md.

  --state, the free canary: gather and print the state, nothing
    else. No model call, no draft, no cost. The wiring proof the
    activity ends phase 2 on, and the cheap look you can take any
    time.

Two of the states are honest non-moves, and they are free too: the
runner writes them itself, because there are no words to draft.
NO-PR-YET points you back at your own ship-gate's report (that list
is already your next move, unchanged), and NOTHING-NEW (the state
AND your playbook are identical to your last full run's on this PR;
the memory is kept per PR, so a run on one PR never changes how
another is read) says that waiting is the move, and leaves your last
draft in place.

The monitor NEVER POSTS. Its gh calls only ever read (the whole
allowlist is READONLY_GH below; the runner refuses to execute
anything else); the drafted response or nudge lands in a file; and
the words ship only by your own hand (`gh pr comment`), which your
unit-6 voice-guard latches by construction. Two tools from two weeks
meeting on one doorway: the monitor drafts, the guard holds your own
voice rules, and you are the hand in between. The monitor also never
edits your branch: a rebase plan is a plan, not an executed rebase.

Run it on demand, when you come back to the contribution, never on a
schedule: a loop costs money, adds nothing a working session does
not, and drafts age as fast as threads move.

Fail closed, always with the route named: no playbook, or a playbook
still the template, refuses honestly (the unit-4 refusal register,
carried: an empty judgment file binds nothing, and the monitor will
not invent your thresholds at runtime); a missing gh login or a run
from outside a clone exits with the fix quoted; a gh error that is
not the honest no-PR-yet case stops rather than guessing.

The monitor is a live-mode-only seam: nothing invokes it in eval
mode, no eval set ships for it, and it never reads or changes the
scout, the guard, the gate, or the Module 1 harness interfaces.

Honesty note: the monitor reads your PR the way anyone can read a
public PR. It has no special access and takes no action; skipping it
costs you nothing but the look. What it automates is attention, not
judgment: the thresholds are yours, and so is the send.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# The course model pin: every stated behavior was built and checked
# on Sonnet. Do not add a model flag.
MODEL = "sonnet"

# Paths resolve from where this file is installed (~/.claude/pr-monitor/,
# where INSTALL.md's copy puts it), the unit-6/7 convention: the
# runner's home is the .claude directory it sits in.
MONITOR_DIR = Path(__file__).resolve().parent
CLAUDE_DIR = MONITOR_DIR.parent
PLAYBOOK_PATH = MONITOR_DIR / "playbook.md"
TEMPLATE_PATH = MONITOR_DIR / "playbook-template.md"
FORMS_PATH = MONITOR_DIR / "move-forms.md"
LOG_PATH = MONITOR_DIR / "monitor-log.md"
REPORT_PATH = MONITOR_DIR / "run-report.md"
DRAFT_PATH = MONITOR_DIR / "drafted-move.md"
GATE_LOG = CLAUDE_DIR / "ship-gate" / "gate-log.md"

GH_TIMEOUT_S = 45
MODEL_TIMEOUT_S = 600
MAX_THREAD_CHARS = 40_000
MAX_BODY_CHARS = 12_000

# On the first recorded run against a PR, a non-author comment counts
# as feedback only if it is newer than the PR's newest commit; when no
# commit dates are available, this age cap holds instead. An ancient
# bot comment is history, not news.
FIRST_RUN_FEEDBACK_DAYS = 14

# Everything the monitor is allowed to ask gh, in full. Read-only by
# construction (gate answer 1): no write subcommand appears here, and
# gh_read() refuses to run anything not on this list, so "the monitor
# never posts" is enforced in code, not just promised in prose.
READONLY_GH = {("auth", "status"), ("pr", "view"), ("repo", "view")}

PR_FIELDS = ",".join([
    "number", "title", "url", "state", "isDraft", "author",
    "baseRefName", "headRefName", "headRefOid",
    "mergeable", "mergeStateStatus", "reviewDecision",
    "createdAt", "updatedAt", "closedAt", "mergedAt",
    "statusCheckRollup", "comments", "reviews", "commits", "body",
])

# The four playbook sections the template names; the refusal checks
# each one for content of the student's own.
PLAYBOOK_SECTIONS = ["response rules", "staleness thresholds",
                     "nudge etiquette", "walk-away criteria"]


class MonitorStop(Exception):
    """A fail-closed stop; message names the route out."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def sh(args: list[str], cwd=None, timeout: int = 60):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def gh_read(*args: str, cwd=None):
    """Run one gh command from the read-only allowlist. Any other gh
    invocation is refused here, before it exists: the monitor reads
    PR state and does nothing else."""
    if tuple(args[:2]) not in READONLY_GH:
        raise MonitorStop(
            f"the monitor tried to run `gh {' '.join(args[:2])}`, which "
            "is not on its read-only allowlist. That is a bug in the "
            "runner, not your setup; flag a TF. Nothing was run.")
    try:
        return sh(["gh", *args], cwd=cwd, timeout=GH_TIMEOUT_S)
    except FileNotFoundError:
        raise MonitorStop(
            "the gh CLI is not on PATH, so the monitor cannot read your "
            "PR's state. Install GitHub CLI (https://cli.github.com) or "
            "open the terminal where you normally use gh, then run "
            "again.")
    except subprocess.TimeoutExpired:
        raise MonitorStop(
            f"gh {' '.join(args[:2])} timed out after {GH_TIMEOUT_S}s. "
            "Check your connection (or GitHub's status page) and run "
            "again; the monitor reads live state, so it needs the "
            "network.")


def clip(text: str, limit: int, label: str) -> str:
    if len(text) <= limit:
        return text
    return (text[:limit] + f"\n\n[... {label} truncated by the monitor "
            f"at {limit} characters ...]")


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _fingerprint(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def days_ago(iso: str) -> float | None:
    try:
        when = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    return max(0.0, (now - when).total_seconds() / 86400)


def fmt_days(d: float | None) -> str:
    if d is None:
        return "unknown"
    if d < 1:
        return "under a day"
    n = int(d)
    return f"{n} day" + ("" if n == 1 else "s")


# ---------------------------------------------------------------------------
# Install state, playbook, move forms
# ---------------------------------------------------------------------------

def ensure_installed() -> None:
    if MONITOR_DIR.name != "pr-monitor" or CLAUDE_DIR.name != ".claude":
        raise MonitorStop(
            "the pr-monitor is not installed: this copy of monitor.py "
            f"sits in {MONITOR_DIR}, not in ~/.claude/pr-monitor/, so "
            "its playbook, forms, and log paths cannot resolve. Do the "
            "install (INSTALL.md, three commands: a folder copy and the "
            "playbook placement), then run the installed copy: "
            "python3 ~/.claude/pr-monitor/monitor.py --state")


def repo_root(cwd: Path) -> Path:
    try:
        proc = sh(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise MonitorStop(f"git failed ({e}); is git installed?")
    if proc.returncode != 0:
        raise MonitorStop(
            f"{cwd} is not inside a git clone. Run the monitor from the "
            "clone of the repository your contribution lives in, on your "
            "branch: it reads the PR for the branch you are on, the same "
            "convention as the gate.")
    return Path(proc.stdout.strip())


def current_branch(root: Path) -> str:
    proc = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    if proc.returncode != 0:
        raise MonitorStop("could not read the current branch: "
                          f"{proc.stderr.strip()[:200]}")
    return proc.stdout.strip()


def ensure_gh_auth(root: Path) -> None:
    proc = gh_read("auth", "status", cwd=root)
    if proc.returncode != 0:
        said = (proc.stderr or proc.stdout or "").strip()
        raise MonitorStop(
            "gh is not logged in, so the monitor cannot read your PR's "
            f"state. gh said:\n{said[:400]}\nRun `gh auth status` "
            "yourself to see it, log in with `gh auth login`, then run "
            "the monitor again.")


def _sections(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).lower()
            out[current] = ""
            continue
        if current is not None:
            out[current] += line + "\n"
    return out


def _section_has_content(body: str) -> bool:
    stripped = strip_comments(body)
    return any(ln.strip() and not ln.lstrip().startswith("#")
               for ln in stripped.splitlines())


def load_playbook() -> str:
    if not PLAYBOOK_PATH.is_file():
        raise MonitorStop(
            f"no playbook at {PLAYBOOK_PATH}. The playbook is the part "
            "you write: place it from the template "
            f"(cp {TEMPLATE_PATH} {PLAYBOOK_PATH}), fill its four "
            "sections in your own words, then run again. The monitor "
            "will not invent your thresholds at runtime.")
    text = PLAYBOOK_PATH.read_text(encoding="utf-8", errors="replace")
    sections = _sections(strip_comments(text))
    empty = []
    for wanted in PLAYBOOK_SECTIONS:
        key = next((k for k in sections if k.startswith(wanted)), None)
        if key is None or not _section_has_content(sections[key]):
            empty.append(wanted)
    if empty:
        raise MonitorStop(
            "REFUSAL. Your playbook still has template sections with no "
            f"rules of yours: {'; '.join(empty)}. No rules, no monitor: "
            "an empty judgment file binds nothing (the unit-4 refusal "
            "register, carried), and a drafted nudge with no threshold "
            "behind it would be the monitor's judgment, not yours. Fill "
            f"the sections in {PLAYBOOK_PATH}, under a page, then run "
            "again. The free canary (--state) works now: state reading "
            "needs no judgment.")
    return text


def load_form(name: str) -> str:
    if not FORMS_PATH.is_file():
        raise MonitorStop(
            f"the move forms are missing ({FORMS_PATH}). The package is "
            "incomplete: re-do the install's folder copy from your Week "
            "8 materials (INSTALL.md section 1); your playbook.md is "
            "safe, the copy never touches it.")
    sections = _sections(
        FORMS_PATH.read_text(encoding="utf-8", errors="replace"))
    key = next((k for k in sections if k.startswith(name.lower())), None)
    if key is None or not sections[key].strip():
        raise MonitorStop(
            f"the move form '{name}' is missing from {FORMS_PATH}. The "
            "package is incomplete: re-do the install's folder copy "
            "(INSTALL.md section 1); your playbook.md is safe.")
    return sections[key].strip()


# ---------------------------------------------------------------------------
# State gathering (read-only) and classification
# ---------------------------------------------------------------------------

_NO_PR_RE = re.compile(r"(?i)no pull requests found|no default branch|"
                       r"could not find any pull request")


def resolved_repo(root: Path) -> str:
    """The repository gh resolves from this clone's remotes, which is the
    repository every `gh pr` call below reads. A no-PR answer that does
    not name it is a true statement about a repository you may not have
    meant to ask about."""
    proc = gh_read("repo", "view", "--json", "nameWithOwner", cwd=root)
    if proc.returncode != 0:
        return "(gh resolved no repository from this clone's remotes)"
    try:
        return json.loads(proc.stdout).get("nameWithOwner") or "(unknown)"
    except json.JSONDecodeError:
        return "(unknown)"


def gather_state(root: Path, branch: str) -> dict | None:
    """The PR for the current branch as gh reports it, or None for the
    honest no-PR-yet case."""
    proc = gh_read("pr", "view", "--json", PR_FIELDS, cwd=root)
    if proc.returncode != 0:
        said = (proc.stderr or proc.stdout or "").strip()
        if _NO_PR_RE.search(said):
            return None
        raise MonitorStop(
            "gh could not read a PR for this branch, and not for the "
            f"honest no-PR-yet reason. gh said:\n{said[:400]}\nFix what "
            "it names (auth, network, or the repo context) and run "
            "again; the monitor stops rather than guessing at state.")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise MonitorStop(f"gh returned PR state the monitor could not "
                          f"parse ({e}). Re-run; flag a TF if it "
                          "repeats.")


def summarize_checks(rollup) -> tuple[str, int, int, int]:
    """(summary line, failing, pending, passing) from statusCheckRollup,
    which mixes CheckRun and StatusContext shapes. Non-failure
    conclusions (CANCELLED, SKIPPED, NEUTRAL) never count as failing:
    an old cancelled run is not trouble, and must never route a quiet
    PR to a rebase plan. They are not passes either; the summary line
    names them for what they are."""
    if not rollup:
        return "no checks reported", 0, 0, 0
    failing = pending = passing = notrun = 0
    for item in rollup:
        concl = (item.get("conclusion") or item.get("state") or "").upper()
        status = (item.get("status") or "").upper()
        if concl in ("FAILURE", "ERROR", "TIMED_OUT",
                     "ACTION_REQUIRED", "STARTUP_FAILURE"):
            failing += 1
        elif concl in ("NEUTRAL", "SKIPPED", "CANCELLED"):
            notrun += 1
        elif concl == "SUCCESS":
            passing += 1
        elif status in ("QUEUED", "IN_PROGRESS", "PENDING", "WAITING") \
                or concl in ("", "PENDING", "EXPECTED"):
            pending += 1
        else:
            passing += 1
    parts = []
    if failing:
        parts.append(f"{failing} failing")
    if pending:
        parts.append(f"{pending} pending")
    if passing:
        parts.append(f"{passing} passing")
    if notrun:
        parts.append(f"{notrun} skipped or cancelled")
    return ", ".join(parts) or "no checks reported", failing, pending, \
        passing


def thread_events(pr: dict) -> list[dict]:
    """Comments and reviews, oldest first, normalized."""
    events = []
    for c in pr.get("comments") or []:
        events.append({"kind": "comment",
                       "who": (c.get("author") or {}).get("login", "?"),
                       "when": c.get("createdAt", ""),
                       "text": c.get("body", "")})
    for r in pr.get("reviews") or []:
        state = (r.get("state") or "").replace("_", " ").lower()
        events.append({"kind": f"review ({state})" if state else "review",
                       "who": (r.get("author") or {}).get("login", "?"),
                       "when": r.get("submittedAt")
                       or r.get("createdAt", ""),
                       "text": r.get("body", "")})
    events.sort(key=lambda e: e["when"])
    return events


def playbook_fingerprint() -> str:
    """The filled playbook joins the run fingerprint: a revised
    threshold is a changed input, and nothing-new must never hide a
    revision (the playbook is the one part of this tool the student
    writes)."""
    try:
        return _fingerprint(PLAYBOOK_PATH.read_text(encoding="utf-8",
                                                    errors="replace"))
    except OSError:
        return "no-playbook"


def state_fingerprint(pr: dict) -> str:
    """The mergeability fields are deliberately absent: GitHub computes
    them lazily, so they are compared transition-aware (see
    mergeability_news) instead of hashed into the fingerprint."""
    basis = json.dumps([
        pr.get("state"), pr.get("headRefOid"), pr.get("updatedAt"),
        pr.get("reviewDecision"), len(pr.get("comments") or []),
        len(pr.get("reviews") or []),
        summarize_checks(pr.get("statusCheckRollup"))[0],
        playbook_fingerprint(),
    ], sort_keys=True)
    return _fingerprint(basis)


def mergeability_pair(pr: dict) -> str:
    return (f"{pr.get('mergeable') or 'UNKNOWN'}/"
            f"{pr.get('mergeStateStatus') or 'UNKNOWN'}")


def mergeability_news(prev: str | None, cur: str) -> bool:
    """Whether the mergeability lines changed in a way that counts.
    GitHub computes mergeability lazily, so a value filling in from
    UNKNOWN (or draining back to it) is the computation changing, not
    the PR: only a known-to-known flip (MERGEABLE to CONFLICTING,
    CLEAN to DIRTY) defeats nothing-new."""
    if prev is None:
        return False
    for p, c in zip(prev.split("/"), cur.split("/")):
        if p != "UNKNOWN" and c != "UNKNOWN" and p != c:
            return True
    return False


def latest_commit_when(pr: dict) -> str | None:
    """ISO stamp of the PR's newest commit, or None."""
    dates = [c.get("committedDate") or c.get("authoredDate") or ""
             for c in (pr.get("commits") or [])]
    dates = [d for d in dates if d]
    return max(dates) if dates else None


_LOG_HEADER_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \[(\w+)\] (.*)$")
_LOG_FP_RE = re.compile(r"^- state fingerprint: (\S+)$")
_LOG_MERGE_RE = re.compile(r"^- mergeability: (\S+)$")


def last_full_run(where: str) -> tuple[str | None, str | None,
                                       str | None]:
    """(fingerprint, stamp, mergeability pair) of the newest [run]
    block FOR THIS PR, or (None, None, None). The log is one file,
    but the memory is keyed per repo + PR (the header's URL), so a
    run on one PR never changes how another is read. Free canaries
    ([state] blocks) never count: a look is not a run, so a canary
    right before a full run cannot turn the run into nothing-new."""
    try:
        text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None, None
    fp = stamp = merge = None
    in_match = False
    for line in text.splitlines():
        m = _LOG_HEADER_RE.match(line)
        if m:
            in_match = (m.group(2) == "run"
                        and m.group(3).strip() == where)
            if in_match:
                stamp, fp, merge = m.group(1), None, None
            continue
        if in_match:
            m = _LOG_FP_RE.match(line)
            if m:
                fp = m.group(1)
            m = _LOG_MERGE_RE.match(line)
            if m:
                merge = m.group(1)
    return fp, stamp, merge


def _stamp_to_days(stamp: str | None) -> float | None:
    """Days since a log stamp (local naive '%Y-%m-%d %H:%M')."""
    if not stamp:
        return None
    try:
        when = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    when = when.astimezone()
    now = datetime.datetime.now().astimezone()
    return max(0.0, (now - when).total_seconds() / 86400)


def classify(pr: dict, prev_fp: str | None, prev_stamp: str | None,
             prev_merge: str | None = None) -> tuple[str, str,
                                                     list[str]]:
    """(state id, one honest line, secondary notes). The state ids are
    the lecture's card grid; one move per run, the rest noted.

    Feedback-in means the ball is plausibly in the author's court: a
    reviewer has requested changes, the newest thread event is a
    non-author review that is not an approval, or a non-author comment
    has arrived since the last full run on this PR (on the first run,
    since the PR's newest commit, with FIRST_RUN_FEEDBACK_DAYS as the
    cap when commit dates are unavailable: an ancient comment is
    history, not news). An old acknowledged comment with nothing new
    behind it is quiet, not feedback: the clock, and the author's own
    threshold, own it."""
    notes: list[str] = []
    author = (pr.get("author") or {}).get("login", "")
    # Nothing-new outranks every state, terminal states included: an
    # unchanged merged or closed PR answers free like any other
    # unchanged state (re-checking must never bill a repeat draft).
    # Mergeability is compared transition-aware: a lazy fill-in from
    # UNKNOWN is not news; a known-to-known flip is.
    if prev_fp is not None and state_fingerprint(pr) == prev_fp \
            and not mergeability_news(prev_merge, mergeability_pair(pr)):
        return "nothing-new", ("nothing has changed since your last "
                               "full run (the PR's state and your "
                               "playbook both)"), notes
    if pr.get("mergedAt") or pr.get("state") == "MERGED":
        return "merged", "the PR is merged", notes
    if pr.get("state") == "CLOSED":
        return "closed", "the PR was closed without merging", notes

    checks_line, failing, _, _ = summarize_checks(
        pr.get("statusCheckRollup"))
    conflicts = (pr.get("mergeable") == "CONFLICTING"
                 or pr.get("mergeStateStatus") == "DIRTY")
    events = thread_events(pr)
    others = [e for e in events if e["who"] and e["who"] != author]
    newest = events[-1] if events else None
    last_run_days = _stamp_to_days(prev_stamp)

    feedback = pr.get("reviewDecision") == "CHANGES_REQUESTED"
    if not feedback and newest and newest["who"] != author \
            and newest["kind"].startswith("review") \
            and "approved" not in newest["kind"]:
        feedback = True
    if not feedback and others:
        newest_other_days = days_ago(others[-1]["when"])
        if newest_other_days is not None:
            if last_run_days is not None:
                if newest_other_days < last_run_days:
                    feedback = True
            else:
                # First recorded run on this PR: only a comment newer
                # than the PR's newest commit is news (fallback: the
                # age cap).
                commit_days = days_ago(latest_commit_when(pr) or "")
                bound = (commit_days if commit_days is not None
                         else FIRST_RUN_FEEDBACK_DAYS)
                if newest_other_days < bound:
                    feedback = True

    if conflicts:
        notes.append("the branch has merge conflicts with "
                     f"{pr.get('baseRefName', 'the base')}")
    if failing:
        notes.append(f"checks: {checks_line}")
    if feedback:
        last = others[-1] if others else None
        line = "review feedback is in"
        if pr.get("reviewDecision") == "CHANGES_REQUESTED":
            line = "a reviewer has requested changes"
        if last:
            line += (f" (latest from the thread: {last['kind']} "
                     f"{fmt_days(days_ago(last['when']))} ago)")
        # Feedback outranks branch mechanics: a stranger is waiting on
        # words; the notes carry the rest.
        return "feedback-in", line, notes
    if conflicts or failing:
        reason = ("merge conflicts with the base"
                  if conflicts else f"failing checks ({checks_line})")
        return "branch-stale", f"the branch needs work: {reason}", notes

    last_when = others[-1]["when"] if others else pr.get("createdAt", "")
    quiet = days_ago(last_when)
    return "quiet", (f"the thread is quiet: {fmt_days(quiet)} since the "
                     "last activity by anyone but you"), notes


# Which move form each state folds in; the two non-moves are handled
# before this table is consulted.
MOVE_FOR_STATE = {
    "merged": "merged follow-up",
    "closed": "review response",
    "feedback-in": "review response",
    "branch-stale": "rebase plan",
    "quiet": "polite nudge",
}


def gate_log_note() -> str:
    """The no-PR-yet pointer, honest about whether the gate's log is
    actually on this machine."""
    if GATE_LOG.exists():
        return f"`{GATE_LOG}` holds every run, newest block last"
    return (f"the gate's log `{GATE_LOG}` is not on this machine, so "
            "open your latest gate report wherever you kept it")


def move_from_draft(drafted: str, form_name: str) -> str:
    """The recorded move is the draft's own MOVE line (the prompt
    mandates one): a nudge form that correctly produced a wait note
    is logged as the wait note, never as a nudge the author did not
    make, and the closed close-out is named as itself. The form is
    named alongside so the trail shows both."""
    first = drafted.splitlines()[0].strip() if drafted else ""
    if first.upper().startswith("MOVE:"):
        made = first[len("MOVE:"):].strip()
        if made:
            return f"{made} (via the {form_name} form)"
    return f"{form_name} form (the draft carries no MOVE line)"


# ---------------------------------------------------------------------------
# The report, the draft, the log
# ---------------------------------------------------------------------------

def state_report(root: Path, branch: str, pr: dict | None,
                 state: str, line: str, notes: list[str]) -> str:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    utc = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    # The heading keeps local time so it lines up with monitor-log.md; the
    # run line carries the zoned instant, so every time in this report can
    # be compared with the zoned times GitHub returns.
    out = [f"# PR-monitor run report ({stamp})", "",
           f"- run at: {utc}"]
    if pr is None:
        repo = resolved_repo(root)
        out += [
            f"- clone: {root}",
            f"- repository gh resolved from this clone: {repo}",
            f"- branch: {branch}",
            "- state: NO PR YET (no pull request found for this "
            f"branch in {repo})",
            "",
            "An honest state, and its move is already written: your "
            "ship-gate's latest report is your next-step list, "
            f"unchanged ({gate_log_note()}). The monitor has "
            "nothing to watch until the gate passes and you open the "
            "PR; nothing here is behind.",
            "",
            "Know your PR exists? Then read the repository line "
            "above first: gh resolves it from this clone's remotes, "
            "so a clone of your fork looks for the PR in the fork, "
            "where it does not live. Add the repository the PR "
            "targets as a remote (`git remote add upstream <repo "
            "URL>`) and run again. If the repository is right, gh "
            "could not map this branch to the PR: `gh pr checkout "
            "<number>` puts you on a branch it can map.",
        ]
        return "\n".join(out) + "\n"
    checks_line, _, _, _ = summarize_checks(pr.get("statusCheckRollup"))
    events = thread_events(pr)
    out += [
        f"- PR: {pr.get('url', '?')} ({pr.get('title', '')!r})",
        f"- branch: {pr.get('headRefName', branch)} -> "
        f"{pr.get('baseRefName', '?')}",
        # Absolute times as well as relative ones. A threshold question
        # ("when would fourteen days of silence be up?") cannot be
        # answered from "under a day ago", and a drafting pass asked for
        # a date it was never given will supply one.
        f"- opened: {pr.get('createdAt', '') or '?'} "
        f"({fmt_days(days_ago(pr.get('createdAt', '')))} ago)",
        f"- last activity: {pr.get('updatedAt', '') or '?'} "
        f"({fmt_days(days_ago(pr.get('updatedAt', '')))} ago)",
        f"- checks: {checks_line}",
        f"- mergeable: {pr.get('mergeable', 'UNKNOWN')} "
        f"(merge state {pr.get('mergeStateStatus', 'UNKNOWN')})",
        f"- review decision: {pr.get('reviewDecision') or 'none yet'}",
        f"- thread: {len(events)} comment(s)/review(s)",
        f"- state: {state.upper()}: {line}",
    ]
    for n in notes:
        out.append(f"- also true: {n}")
    return "\n".join(out) + "\n"


def write_log(mode: str, root: Path, branch: str, pr: dict | None,
              state: str, line: str, move: str) -> None:
    if MONITOR_DIR.name != "pr-monitor" or CLAUDE_DIR.name != ".claude":
        return      # an uninstalled copy never writes a log beside itself
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    where = pr.get("url", "?") if pr else f"{root.name} @ {branch}"
    lines = [f"## {stamp} [{mode}] {where}", "",
             f"- state: {state}: {line}",
             f"- move: {move}"]
    if pr is not None:
        lines.append(f"- state fingerprint: {state_fingerprint(pr)}")
        lines.append(f"- mergeability: {mergeability_pair(pr)}")
    lines.append("")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            if f.tell() == 0:
                f.write("# pr-monitor log (one dated block per run; "
                        "the free canary logs as [state])\n\n")
            f.write("\n".join(lines) + "\n")
    except OSError:
        pass


PROMPT_TEMPLATE = """You are the pr-monitor's drafting pass: one print-mode call, run
headless, drafting the matching next move for a real open-source
contribution. You draft; you never post. The author revises every
word into their own voice and ships it through their own guarded
doorway, so write a draft worth revising, not a final text.

Below are (1) the author's PLAYBOOK, their own rules for responding
to review, for staleness and nudging, and for walking away; (2) the
MOVE FORM staff wrote for this state, which is the frame your draft
fills; (3) the PR's gathered state and thread. Follow the form's
instructions exactly, and let the playbook's rules override any
general instinct: where the playbook states a threshold or a rule,
that rule decides, and your draft should say (in a bracketed note,
not in the draft body) which playbook rule drove the call.

Hard rules, from the course, never overridden: never defensive (open
by answering the actual point, thank precisely, disagree only with
evidence, never explain why the mistake was reasonable); one
self-contained message, no @-piles; nothing in the draft may claim
work that was not done or state you cannot see. If the form says the
right output is NOT to send anything (a threshold unmet, a wait),
say so plainly and write the short wait note instead.

Output exactly this shape: one line `MOVE: <what this draft is>`,
then a blank line, then the draft (or the wait note) in plain
markdown, then a blank line and any bracketed notes to the author.
No other commentary.

=== THE AUTHOR'S PLAYBOOK ===
{playbook}

=== THE MOVE FORM ({move}) ===
{form}

=== THE PR'S STATE, AS GATHERED ===
{report}

=== THE PR DESCRIPTION ===
{body}

=== THE THREAD, OLDEST FIRST ===
{thread}
"""


def render_thread(pr: dict) -> str:
    events = thread_events(pr)
    if not events:
        return "(no comments or reviews yet)"
    parts = []
    for e in events:
        when = fmt_days(days_ago(e["when"]))
        parts.append(f"--- {e['kind']} by {e['who']}, {when} ago ---\n"
                     f"{e['text'] or '(no text)'}")
    return clip("\n\n".join(parts), MAX_THREAD_CHARS, "thread")


def run_draft(playbook: str, move: str, form: str, report: str,
              pr: dict) -> str:
    prompt = PROMPT_TEMPLATE.format(
        playbook=playbook, move=move, form=form, report=report,
        body=clip(pr.get("body") or "(no description)", MAX_BODY_CHARS,
                  "PR description"),
        thread=render_thread(pr))
    # Spawn on the subscription login, never an API key (the course's
    # standing headless-spawn convention).
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    print(f"pr-monitor: drafting via the {move} form (one {MODEL} "
          "call; the draft's MOVE line names the move it makes)...",
          file=sys.stderr, flush=True)
    last_err = None
    for _ in range(2):
        try:
            proc = subprocess.run(["claude", "-p", "--model", MODEL],
                                  input=prompt, capture_output=True,
                                  text=True, timeout=MODEL_TIMEOUT_S,
                                  env=env)
        except FileNotFoundError:
            raise MonitorStop(
                "the claude CLI is not on PATH, so nothing can be "
                "drafted. The state gathering still works: run --state "
                "for the free look, and draft by hand if you need to "
                "move now.")
        except subprocess.TimeoutExpired:
            last_err = f"the drafting call timed out ({MODEL_TIMEOUT_S}s)"
            continue
        if proc.returncode != 0:
            said = (proc.stderr or proc.stdout or "").strip()
            last_err = f"claude exited {proc.returncode}: {said[-240:]}"
            continue
        if proc.stdout.strip():
            return proc.stdout.strip()
        last_err = "the drafting call returned nothing"
    raise MonitorStop(
        f"the drafting pass could not complete ({last_err}). Nothing "
        "was drafted and nothing was posted; run again, or flag a TF "
        "if it repeats. --state still shows you the state for free.")


# ---------------------------------------------------------------------------
# The runs
# ---------------------------------------------------------------------------

def preflight() -> tuple[Path, str]:
    ensure_installed()
    root = repo_root(Path.cwd())
    branch = current_branch(root)
    ensure_gh_auth(root)
    return root, branch


def state_run() -> int:
    """--state: the free canary. Gather and print; no model call, no
    draft, no playbook needed (state reading needs no judgment)."""
    root, branch = preflight()
    pr = gather_state(root, branch)
    if pr is None:
        state, line, notes = "no-pr-yet", "no PR found for this branch", []
    else:
        # The canary reports the PR itself, never your run history:
        # prev_fp stays None so nothing-new cannot become the headline
        # state of a look (a look is not a run).
        _, prev_stamp, _ = last_full_run(pr.get("url", "?"))
        state, line, notes = classify(pr, None, prev_stamp)
    report = state_report(root, branch, pr, state, line, notes)
    print(report)
    print("pr-monitor: state only; no model call was made and nothing "
          "was drafted. A full run (no flag) drafts the matching move.")
    write_log("state", root, branch, pr, state, line,
              "none (state-only canary)")
    return 0


NON_MOVE_TEXT = {
    "no-pr-yet": (
        "## The move: your gate report, unchanged\n\n"
        "No PR was found for this branch, and that is an honest place "
        "to be. The next-step list already exists and the monitor "
        "will not re-derive it: read your ship-gate's latest report "
        "({gate_note}). Whatever it quoted is the move; when the gate "
        "passes and you open the PR, the monitor has something to "
        "watch.\n"),
    "nothing-new": (
        "## The move: wait\n\n"
        "The state is identical to your last full run's on this PR "
        "({stamp}): "
        "same head, same thread, same checks, same playbook. Waiting "
        "is the move; a re-draft of the same state would say the same "
        "thing for real money. drafted-move.md is untouched (the "
        "draft from that run still stands). Come back when something "
        "changes, or take the free look any time with --state.\n"),
}


def full_run() -> int:
    root, branch = preflight()
    playbook = load_playbook()
    pr = gather_state(root, branch)

    draft = None
    if pr is None:
        state, line, notes = "no-pr-yet", "no PR found for this branch", []
        report = state_report(root, branch, pr, state, line, notes)
        draft = NON_MOVE_TEXT["no-pr-yet"].format(gate_note=gate_log_note())
        move = "no-PR-yet (non-move, free: points at your gate report)"
    else:
        prev_fp, prev_stamp, prev_merge = last_full_run(
            pr.get("url", "?"))
        state, line, notes = classify(pr, prev_fp, prev_stamp,
                                      prev_merge)
        report = state_report(root, branch, pr, state, line, notes)
        if state == "nothing-new":
            # Free, and the last draft stays put: a wait must never
            # overwrite the draft the author is still revising.
            move = "nothing-new (non-move, free: wait)"
        else:
            form_name = MOVE_FOR_STATE[state]
            form = load_form(form_name)
            drafted = run_draft(playbook, form_name, form, report, pr)
            move = move_from_draft(drafted, form_name)
            stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            draft = (f"# Drafted move ({stamp}): {move}\n\n"
                     "> A DRAFT by design. Nothing has been posted, and "
                     "nothing will be unless you post it: revise it "
                     "into your own words, then ship it yourself "
                     "(`gh pr comment`), through your own guard.\n\n"
                     f"{drafted}\n")

    REPORT_PATH.write_text(report, encoding="utf-8")
    if draft is not None:
        DRAFT_PATH.write_text(draft, encoding="utf-8")
    write_log("run", root, branch, pr, state, line, move)
    print(report)
    if state == "nothing-new":
        print(NON_MOVE_TEXT["nothing-new"].format(
            stamp=prev_stamp or "unlogged"))
    print(f"pr-monitor: run report -> {REPORT_PATH}")
    if draft is not None:
        print(f"pr-monitor: drafted move ({move}) -> {DRAFT_PATH}")
    else:
        print(f"pr-monitor: drafted-move.md untouched; the draft from "
              "your last run still stands.")
    if state not in ("no-pr-yet", "nothing-new"):
        print("pr-monitor: the draft is a draft. Revise it into your "
              "own words before anything ships; posting is your hand, "
              "through your guard.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(
        "pr-monitor: read your contribution's live state (read-only) "
        "and draft the matching next move. Run from inside your clone, "
        "on your branch. --state is the free canary."))
    ap.add_argument("--state", action="store_true",
                    help="gather and print the state only: no model "
                         "call, no draft, no cost (the wiring canary)")
    args = ap.parse_args()
    try:
        return state_run() if args.state else full_run()
    except MonitorStop as e:
        print(f"pr-monitor: STOP. {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
