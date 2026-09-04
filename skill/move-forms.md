# Move forms (staff-complete; the monitor folds one in per run)

<!--
These are the frames the monitor's one drafting call fills, one per
post-ship state. Staff wrote the frames; your playbook's rules decide
inside them, and every drafted word is a draft until you revise it
and ship it yourself through your guard. The runner reads exactly one
section per run, matched by its heading; do not rename the headings.
The two non-move states (no PR yet, nothing new) never reach a form:
the runner writes those itself, free, because there are no words to
draft.
-->

## Review response (never defensive)

Draft the response to the newest unanswered review feedback in the
thread, one comment or review round at a time, in this order and
shape:

- Open by answering the reviewer's actual point: the substance first,
  never a preamble, never an apology tour. If the reviewer is right,
  say what you will change (or changed) and where. If you disagree,
  disagree once, with evidence the reviewer can check (a line, a test,
  a doc), and offer to defer to their call.
- Thank precisely: for the specific catch or the specific time, not
  for "the feedback". One sentence at most.
- Never explain why the mistake was reasonable, how busy you were, or
  how a tool misled you. The reviewer is deciding whether to keep
  investing attention; the response is the evidence.
- If the round has several comments, answer every one in the same
  message (a fix, a question, or a reasoned no for each); note in a
  bracketed author-note that pushes should be batched so the reviewer
  reads once, and that re-review is requested only when the whole
  round is addressed.
- Apply the playbook's Response rules on top of all of this; where
  the author's rule is stricter, the author's rule wins.

For a PR the maintainer CLOSED: the same form drafts the close-out.
Answer the stated closing reason without arguing it, thank precisely,
and, if the author's Walk-away criteria say this is the end, close
with one honest sentence recording that. A closed PR cost the author
nothing: the score was banked when it opened.

## Rebase plan

Draft a PLAN, never commands to be executed blind and never an
executed rebase. The branch needs work (conflicts with the base, or
failing checks); lay out:

- What changed under the branch: name the base branch and what the
  gathered state shows (conflicting files are not visible to the
  monitor; say what the author should look at).
- The safe order, as steps the author runs on their own fork branch:
  fetch the upstream base, rebase the branch onto it, resolve what
  git flags, re-run the ship-gate (their manifest's checks and their
  own rubric), then force-push to their fork with
  `git push --force-with-lease`. Guest work: none of this needs
  anyone's permission, and nothing is lost while the branch exists.
- For failing checks: read the check's own output first; the fix goes
  in a normal commit, and the batched-push rule applies if a review
  round is also open.
- End with the state this plan should produce (a green, mergeable
  branch) and the reminder that the gate is still on the door for
  anything that ships.

## Polite nudge

First, apply the playbook's Staleness thresholds to the gathered
quiet time. If the threshold is NOT met, the right output is no
nudge: write a short wait note instead, quoting the author's own
threshold rule, and say when the threshold would be met. Drafting a
nudge the author's own rules forbid is a failure of this form.

If the threshold is met, draft ONE message:

- Self-contained: a stranger reading only this comment knows what the
  PR does and what is being asked (one sentence of each). Never
  assume the reader remembers the thread.
- One ask, and only one: a review, a re-review, or an answer to one
  named question.
- No @-pile, no urgency theater, no guilt. The unit-6 claim-craft
  rules carry unchanged: maintainer time is a gift, silence is
  usually a queue, and one polite surfacing is the entire move.
- Apply the playbook's Nudge etiquette on top; the author's rules
  win where stricter.

## Merged follow-up

The PR is merged. Draft the short close of the loop:

- Thanks, precise and once: to whoever reviewed and merged, for the
  specific attention.
- The loop noted: if the linked issue did not auto-close, note that
  it can be closed and say why (the fix is in); if anything was left
  deliberately out of scope, name it honestly as a possible follow-up
  issue, without volunteering for it in this message.
- Nothing else. A merged thread is a finished conversation; the
  author's record keeping (the round-1 README's Status line and
  Maintainer Feedback log, the unit-8 Toolkit entry) happens in the
  course repo, not in the maintainer's thread.
- In the bracketed author-notes, not in the draft: a second
  contribution is welcome now that the loop is cheap, never required,
  never graded; `round-template/` in the course repo copies to
  `round2/` if the author wants the record kept in the same place.
