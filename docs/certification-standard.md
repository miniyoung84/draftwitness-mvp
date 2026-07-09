# DraftWitness — Certification Standard

This document defines the certification levels and statuses used by DraftWitness.
The language here is deliberately careful: DraftWitness certifies a **recorded
process**, never metaphysical certainty and never "AI detection."

## Human-Origin Verified

The default certification level (`certification_level = "Human-Origin Verified"`).

**Meaning:** A human reviewer examined the recorded drafting evidence for the
work and found it consistent with a work drafted by a person inside the
DraftWitness workflow, and the event hash chain verified intact at the time of
issuance.

**Basis of evidence:**
- one or more recorded drafting sessions,
- a tamper-evident, hash-chained event log,
- checkpoint and text-change events showing incremental drafting,
- disclosed paste events (recorded, not disqualifying on their own).

**Explicitly not implied:** that no AI tool was ever used anywhere in the
author's broader process. It is a *process* verification, not an absolute claim.

## Process Verified

A description of what every DraftWitness certificate fundamentally attests: the
**drafting process was recorded and its integrity is verifiable**. "Human-Origin
Verified" is the reviewer-attested level built on top of "Process Verified"
evidence. Use "Process Verified" when referring to the evidentiary foundation
(the hash chain and event log) independent of reviewer judgment.

## Inconclusive

**Meaning:** A reviewer examined the evidence but could not reach a confident
approval or denial. Common causes: too little recorded drafting activity, a
large share of pasted content with no in-system drafting, or an event history
too sparse to assess.

**Effect:** No certificate is issued. The author may add more recorded drafting
and resubmit. "Inconclusive" is a neutral state, not an accusation.

## Revoked

**Meaning:** A previously issued certificate has been withdrawn. A certificate
may be revoked if, for example, the underlying event chain is later found to be
broken, the review was made in error, or evidence of workflow abuse emerges.

**Effect:** The public certificate page shows `status = revoked` with a
`revoked_at` timestamp. The certificate ID remains resolvable so that anyone
holding the link sees the revocation rather than a dead page.

## Status vs. level

- **Certification level** describes *what was verified* (e.g. "Human-Origin
  Verified").
- **Certificate status** describes the *current validity* of the certificate
  (`active` or `revoked`).
- **Project status** (`draft`, `submitted`, `approved`, `denied`,
  `inconclusive`, `certified`) tracks the work's position in the workflow.
