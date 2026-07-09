# DraftWitness — Threat Model (v0)

DraftWitness certifies a **recorded drafting process**. This document lists the
attacks most likely to matter and states plainly what v0 mitigates and what it
does not. Being honest about the gaps is part of the product: we never claim
"AI-free guaranteed."

## Attack 1 — User pastes AI-generated text into the editor

**What v0 does:** The editor detects paste events and records `paste_detected`
events (character count, word count, timestamp) into the tamper-evident log.
Reviewers see paste count and pasted-character totals in the evidence summary.

**What v0 does NOT do:** It does not block pasting and does not judge whether
pasted text is AI-generated. A work that is largely pasted is *visible* to the
reviewer as such; the reviewer decides. There is no AI detection.

## Attack 2 — User types AI-generated text manually (retyping / dictation)

**What v0 does:** Records incremental typing as `text_changed` and
`checkpoint_created` events, producing a plausible drafting timeline.

**What v0 does NOT do:** It cannot distinguish a human composing original text
from a human transcribing text produced elsewhere. This is a fundamental limit
of process monitoring and the central reason we make no absolute-origin claim.
Mitigations (keystroke-timing analysis, revision-pattern heuristics) are future
work and are still only *signals*, never proof.

## Attack 3 — User edits database rows to fake or alter history

**What v0 does:** Each `EventLog` row stores a SHA-256 `event_hash` computed over
its canonical fields **including the previous event's hash**. Editing any
historical payload, or reordering/removing events, breaks the chain.
`verify_project_chain` detects the break, and the reviewer/history UIs surface a
"broken" verification badge. Certificates are refused for projects whose chain
does not verify.

**What v0 does NOT do:** The hash chain is stored in the same database an
attacker with write access could reach. A sufficiently privileged attacker could
recompute a *fully consistent* forged chain from scratch. v0 does not provide
external anchoring (e.g. periodic notarization or append-only storage) — that is
deliberately out of scope (no blockchain). v0 detects casual/accidental
tampering and single-row edits, not a full-database rewrite by an admin.

## Attack 4 — User creates text outside the app, then imports it

**What v0 does:** Import happens as a paste, which is recorded as a
`paste_detected` event and reflected in the evidence summary, so wholesale
imports are visible to reviewers.

**What v0 does NOT do:** It does not prevent import and cannot vouch for the
origin of externally created text. Certification covers the *recorded* process,
not the pre-history of imported content.

## Attack 5 — Compromised reviewer account

**What v0 does:** Reviewer actions require an authenticated staff account, and
review decisions and certificate issuance are themselves recorded as
`review_decision` / `certificate_issued` events in the hash chain, creating an
audit trail of who decided what.

**What v0 does NOT do:** v0 has minimal role separation (a single `is_staff`
flag), no multi-reviewer consensus, no rate limiting, and no anomaly detection.
A compromised reviewer account can approve work and issue certificates. Hardening
(MFA, least-privilege roles, multi-party review, revocation workflows) is future
work. Revocation exists as a status so bad certificates can be withdrawn after
the fact.

## Summary of v0 posture

| Threat | Detected/Recorded | Prevented | Notes |
| --- | --- | --- | --- |
| Pasted AI text | Yes (recorded) | No | Visible to reviewer, not judged |
| Manually typed AI text | No | No | Fundamental limit; no AI detection |
| DB row tampering | Yes (single edits) | No | Full-DB rewrite by admin not covered |
| External import | Yes (as paste) | No | Origin of imported text unverified |
| Compromised reviewer | Audit trail only | No | Minimal roles in v0; revocation exists |

v0 is an **evidence and process** system, not a guarantee. Its value is a
tamper-evident record plus human review, transparently scoped.
