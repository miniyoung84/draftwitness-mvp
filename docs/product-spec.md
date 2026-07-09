# DraftWitness — Product Spec (MVP)

DraftWitness is a **human-origin certification platform for written creative
work**. It does **not** claim to "detect AI." Instead, it provides a *monitored
writing workflow* that records drafting events, builds a tamper-evident event
history, and — after human review — issues a public certificate.

## The MVP

The MVP delivers one complete vertical slice:

1. A user creates an account and a writing project.
2. The user writes inside the DraftWitness editor.
3. The editor sends drafting events (session start/end, periodic text changes,
   paste detections, 30-second checkpoints) to the backend.
4. The backend records each event in a **hash-chained** event log, so any later
   tampering with the recorded history is detectable.
5. The user submits the project for review.
6. A reviewer (staff user) approves, denies, or marks the project inconclusive.
7. Approved projects can be issued a certificate.
8. A **public certificate page** shows the certificate status and an evidence
   summary that anyone can view.

## What DraftWitness certifies

DraftWitness certifies the **creation process recorded inside the system**:

- that the work was drafted through DraftWitness's monitored editor,
- across one or more recorded drafting sessions,
- with a tamper-evident, hash-chained log of drafting events (typing bursts,
  checkpoints, paste events), and
- that a human reviewer examined that evidence before a certificate was issued.

We describe this as **Witnessed Human-Origin Drafting** / **Process Verified**.

## What DraftWitness does NOT certify

DraftWitness makes **no** claim of "AI-free guaranteed" and performs **no** AI
detection. In particular, it does **not** certify:

- that no AI tool was used anywhere in the author's process,
- the origin of text created outside the DraftWitness editor and pasted in
  (such pastes are *recorded as evidence*, not blocked or judged),
- metaphysical certainty about all possible activity outside the recorded
  workflow, or
- authorship disputes, plagiarism, or copyright ownership.

DraftWitness verifies a **recorded process**, not an absolute claim about a
person's mind or every tool they may have touched.

## Product language

Use: **Human-Origin Verified**, **Process Verified**, **Witnessed Human-Origin
Drafting**.

Avoid: "AI-free guaranteed," "AI detection," or any absolute-certainty claim.

Standard disclaimer shown on certificates:

> This certificate verifies that the work was created through DraftWitness's
> recorded drafting workflow. It is not a claim of absolute certainty about all
> activity outside the recorded workflow.
