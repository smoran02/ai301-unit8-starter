# AI301 Unit 8 starter: the PR-monitor

Materials for Unit 8 of AI301 (keeping it alive). This repo holds the
unit's runnable package: the PR-monitor, a headless runner that reads
your pull request's live state through read-only `gh` calls, folds in
a playbook you write, and drafts the matching next move to a file,
never posting a word itself. All instructions live on the course
portal (Overview, Activity, and Check-In tabs for Unit 8); this repo
is the package those pages tell you to install.

## What's here

- `skill/INSTALL.md`: the whole install (three copy commands), the
  overlay stated loudly in every direction, the no-hook fact with its
  reason (an invoked tool has no doorway to latch), the boundary
  facts (read-only, drafts to files, never posts, on demand, never
  scheduled), the free canary, and the fail-closed list with the
  route out of each stop.
- `skill/monitor.py`: the runner. A full run gathers the PR's live
  state (the runner refuses, in code, to execute anything off its
  read-only allowlist), classifies it, folds in your playbook and the
  matching staff move form, makes one model call, and writes
  `run-report.md` plus `drafted-move.md` beside itself, appending a
  dated block to `monitor-log.md`. `--state` is the free canary:
  gather and print, no model call, works before the playbook exists.
- `skill/move-forms.md`: the staff move forms the drafting call fills
  (the never-defensive review response, the rebase plan, the polite
  nudge, the merged follow-up). Staff-complete; your playbook's rules
  win wherever they are stricter.
- `skill/playbook-template.md`: THE HOLE. A structured template with
  zero content: response rules, staleness thresholds, nudge
  etiquette, walk-away criteria. Installed as `playbook.md`; you
  write every word of it.

## Install

The Activity tab has the full steps and the warnings. In short: get
this repo onto your machine (`git clone
https://github.com/smoran02/ai301-unit8-starter.git`, or Code then
Download ZIP on the repo page), then, from the clone (run the third
command once; skip it if your `playbook.md` already exists):

```
mkdir -p ~/.claude/pr-monitor
cp skill/monitor.py skill/move-forms.md skill/playbook-template.md skill/INSTALL.md ~/.claude/pr-monitor/
cp ~/.claude/pr-monitor/playbook-template.md ~/.claude/pr-monitor/playbook.md
```

No hook and no settings merge: the monitor is invoked, not latched.
Everything you already own (the scout, the guard and your voice
guide, the gate and your manifest, pr-precheck, and every Module 1
folder in your course repo) stays yours and untouched.

Then the free canary, from inside your clone, on your branch. No
model call, no draft, no cost; it prints your PR's real state, or
the honest `NO PR YET`:

```
python3 ~/.claude/pr-monitor/monitor.py --state
```

## No eval/ here, on purpose

Unit 8 ships no eval set and no harness. The monitor reads live PR
state and carries no gold labels; there is nothing to gold-label
without grading the wild. It is a live-mode-only seam: it never runs
in eval mode, and the Module 1 harness interfaces are untouched.
