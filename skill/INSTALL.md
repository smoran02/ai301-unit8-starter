# Installing the pr-monitor (a folder copy, and why that is the whole install)

This install puts the toolkit's last tool in your home: the
pr-monitor, a headless runner that reads your pull request's live
state through read-only `gh` calls and drafts the matching next move
to a file. It is an **overlay onto what you already own**, stated in
every direction:

- **Added:** the monitor, as one folder at `~/.claude/pr-monitor/`:
  the runner `monitor.py` (the full run and the free `--state`
  canary), the staff-complete move forms (`move-forms.md`), and the
  playbook template. All staff-complete; you write no code.
- **Replaced:** nothing.
- **Promoted:** nothing.
- **Yours and untouched:** every installed tool as you left it (the
  scout, the voice-guard and your voice guide, the ship-gate and
  your manifest, pr-precheck and every judgment file of it), your
  Claude Code settings, and every Module 1 folder in your course
  repo's `tools/` exactly as submitted. Re-running this install
  never touches your `playbook.md` either: the copy carries the
  template, not the filled file.

**No hook, and no settings merge, on purpose.** Units 6 and 7 put
latches on doorways: the guard and the gate fire on commands you were
already running, so they had to live in your Claude Code settings.
The monitor has no doorway to latch: it is **invoked, not latched**,
a program you run on demand from any terminal, and a settings entry
would claim a wiring that does not exist. Packaging was last week's
lesson; this week's is that a finished tool can be this small to
install and still be the biggest capability jump of the module: it
runs with no session open at all.

**The boundary facts, before anything else:** the monitor's `gh`
calls only ever read (the runner refuses to execute anything off its
read-only allowlist, in code); drafts land in files, never on
GitHub; it never edits your branch (a rebase plan is a plan); and it
runs on demand, never on a schedule (a loop costs money and drafts
age as fast as threads move). Posting stays your own hand,
`gh pr comment`, where your unit-6 guard holds every word against
your own voice rules. The monitor never runs in eval mode, and no
eval set ships for it.

## 1. The install: three commands

From the folder where you unpacked the Unit 8 materials:

```
mkdir -p ~/.claude/pr-monitor
cp skill/monitor.py skill/move-forms.md skill/playbook-template.md skill/INSTALL.md ~/.claude/pr-monitor/
cp ~/.claude/pr-monitor/playbook-template.md ~/.claude/pr-monitor/playbook.md
```

The third command places your playbook from the template; run it
ONCE. If `~/.claude/pr-monitor/playbook.md` already exists (a
re-install, a second machine syncing), skip it: the playbook is
yours, and overwriting it would delete your judgment. The first two
commands are always safe to re-run; they refresh the staff files and
never touch `playbook.md`.

There is no step 4. No settings change, no fresh-session rule, no
scope swap: nothing else on your machine knows the monitor exists,
which is exactly the shape of an invoked tool.

## 2. Prove the wiring: the free state canary

From inside your clone, on your branch (the monitor reads the PR for
the branch you are on, the same convention as the gate):

```
python3 ~/.claude/pr-monitor/monitor.py --state
```

This gathers and prints your PR's real state: checks, review
decision, thread activity, days of quiet, mergeability, or the
honest `NO PR YET`. **No model call is made and nothing is drafted:
the canary is free**, and it works before your playbook is written
(state reading needs no judgment). Whatever it prints is the wiring
proof, and for many of you it is the first structured look at your
own post-ship state.

A few of the state line's words are GitHub's, not ours, so here is
the gloss: **review decision REVIEW_REQUIRED** means the repo wants a
review before merging and none has landed yet (normal for a fresh
PR); **mergeable** is whether your branch applies cleanly
(CONFLICTING is the rebase-plan case); **merge state BLOCKED** means
GitHub is waiting on required conditions, usually that review, and is
not a verdict on your work; **UNKNOWN** on either mergeability line
means GitHub has not computed the answer yet (it computes lazily, so
a later read filling the value in is the computation finishing, not
your PR changing, and the monitor treats only a known-to-known flip
as news). Two more facts about that line: once a PR is merged, its
checks and mergeability lines stop meaning anything (GitHub stops
keeping them current, so read them as leftovers, not state). And on
the monitor's first run against a PR, only comments newer than your
newest commit count as feedback in (14 days is the cap when commit
dates are unavailable): an old bot comment from before your work is
history, not news.

One honest limit: the monitor finds your PR by the branch you are
standing on. If you know your PR exists and still see `NO PR YET`,
gh could not map the branch to it; `gh pr checkout <number>` puts you
on a branch it can map, then run again.

## 3. A full run, in anger

Fill your playbook first (`~/.claude/pr-monitor/playbook.md`, four
sections, under a page; the monitor refuses on an empty one). Then,
from your clone, on your branch:

```
python3 ~/.claude/pr-monitor/monitor.py
```

One run gathers the state, classifies it, folds in your playbook and
the matching staff move form, makes ONE print-mode Sonnet call, and
writes two files beside the runner: `run-report.md` (the state,
honestly) and `drafted-move.md` (the draft, or the honest non-move).
Every run appends a dated block to `monitor-log.md`. A few cents to
about $0.25 on a long thread; the two non-move states (`NO PR YET`,
`NOTHING NEW`) are written by the runner itself and cost nothing.

Expect a run to take a minute or two when it drafts. Re-running with
an unchanged state AND an unchanged playbook gets the free
`NOTHING NEW` answer rather than a second draft of the same thing,
in every state including merged and closed: waiting is a move, and
the monitor says so instead of billing you to repeat itself. It also
leaves `drafted-move.md` alone on that answer, so the draft you were
revising is still there. Change either input, the PR's state or your
playbook (a revised threshold counts), and the next run drafts
fresh. That memory is kept per PR (one log file, keyed by the PR's
URL): a run against one PR, the house chain's say, never changes how
your own PR's next run is read.

## 4. What stops the monitor, and the route out

Every stop names its route; nothing is ever posted or half-done:

- **Run from an uninstalled copy.** The runner resolves its playbook,
  forms, and log from the folder it is installed in; run the
  installed copy (`~/.claude/pr-monitor/monitor.py`) after section
  1's copy.
- **Not inside a clone.** Run it from the clone of your
  contribution's repo, on your branch: the branch is how it finds
  your PR.
- **gh not logged in (or rate-limited).** The stop quotes what gh
  said; `gh auth status` shows it yourself, `gh auth login` fixes
  the common case, and a rate limit passes on its own. The monitor
  reads live state, so it needs a working gh.
- **No playbook, or a playbook still the template.** The REFUSAL is
  the tool telling the truth, not breaking: an empty judgment file
  binds nothing, and the monitor will not invent your thresholds at
  runtime (the same refusal register your own unit-4 tool taught
  you). Fill the empty sections it names; `--state` works
  meanwhile.
- **A gh error that is not the honest no-PR-yet case.** The stop
  quotes gh's own words; fix what they name and run again. The
  monitor stops rather than guessing at state.
- **The drafting call failed or timed out.** Nothing was drafted and
  nothing was posted; run again, or flag a TF if it repeats.
  `--state` still shows the state for free.

## 5. The evidence trail, and where the words go

`~/.claude/pr-monitor/monitor-log.md` keeps one dated block per run
(state, move, fingerprint); it just grows, a term of runs is small,
and that is fine. `run-report.md` and `drafted-move.md` hold the
latest run, overwritten on each run that drafts (a free
`NOTHING NEW` answer leaves your draft in place), so the log is the
history and the files are the working copy. All of it stays on your
machine: Assignment 5 asks for no monitor output anywhere, and the
unit-8 Toolkit entry in your contribution story, in your own words,
is what the rubric reads. The packaged monitor, self-contained in
this one folder, is unit-9 portfolio material.

When a draft is worth sending, the motion is two steps, and the file
you post is never `drafted-move.md` (that file carries the DRAFT
banner, the MOVE line, and bracketed notes addressed to you, none of
which belong in a maintainer's thread):

1. Write your revision into its own file: open `drafted-move.md`,
   take the draft body, make every word yours, and save the result
   as `~/.claude/pr-monitor/my-reply.md` (any path works; this one
   keeps it beside the tool).
2. Post that file, yourself:

```
claude "run this command: gh pr comment <PR-URL> --body-file ~/.claude/pr-monitor/my-reply.md"
```

Your unit-6 guard fires on that doorway by construction and holds
the words against your own voice rules: the monitor drafted, the
guard checks, and you are the hand in between. Posting from the
browser? Run the guard's manual doorway first, the unit-6 practice,
unchanged.
