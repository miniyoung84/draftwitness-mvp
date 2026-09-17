# DraftWitness — Roadmap

Prioritized next steps for the MVP, written as ready-to-file issues (title,
priority, description, acceptance criteria). This project is no longer under
active development, so these are left here as a record of what a v1 would have
needed. See the [project status](../README.md#project-status) in the README.

Scope guardrails for all issues: **no AI detection, no marketplace, no payments,
no blockchain, no external identity verification, no new third-party
integrations.** DraftWitness verifies a *recorded process*, not metaphysical
certainty.

---

## 1. External anchoring for the hash chain

**Priority:** P1 (highest-value integrity gap)
**Labels:** `backend`, `security`, `integrity`

**Description**
The per-event SHA-256 hash chain (`backend/api/hashchain.py`) detects casual
tampering and single-row edits, but it lives in the same database an attacker
with write access could reach. A sufficiently privileged actor could recompute a
fully consistent forged chain from scratch (see `docs/threat-model.md`, Attack 3).
Add lightweight external anchoring so a full-database rewrite becomes detectable
**without** introducing a blockchain.

Approach: periodically compute a checkpoint digest (e.g. the latest event hash
per project, or a Merkle root across projects) and write it to append-only /
tamper-resistant storage (signed file in object storage, or an append-only audit
table with restricted grants). Store anchor references so verification can prove
the current chain matches what was anchored earlier.

**Acceptance criteria**
- [ ] A scheduled/management command produces a signed checkpoint of chain state.
- [ ] Checkpoints are written to storage separate from the primary app DB.
- [ ] `verify_project_chain` (or a companion) can compare current chain state to
      the most recent anchor and flag divergence.
- [ ] Tests cover: matching anchor passes; a post-anchor history rewrite is
      detected.
- [ ] `docs/threat-model.md` Attack 3 updated to reflect the new mitigation.
- [ ] No blockchain and no external paid service required to run locally.

---

## 2. Certificate revocation workflow

**Priority:** P1
**Labels:** `backend`, `frontend`, `reviewer`

**Description**
The `Certificate` model already supports `status = revoked` and `revoked_at`, but
there is no way to revoke a certificate or to surface revocation on the public
page. Add a reviewer-only revocation endpoint and UI, and ensure the public
certificate page clearly shows a revoked certificate rather than hiding it.

**Acceptance criteria**
- [ ] `POST /api/reviewer/projects/{id}/revoke-certificate/` (staff only) sets
      `status = revoked`, stamps `revoked_at`, and appends a chained event.
- [ ] Reviewer detail page shows a "Revoke certificate" action when a certificate
      is active, with a reason/notes field.
- [ ] Public certificate page (`/certificates/[certificateId]`) shows a clear
      revoked state and `revoked_at`; the ID still resolves (no dead link).
- [ ] Tests: revoke flips status + timestamp, is staff-gated, and the public
      endpoint reflects the revoked status.

---

## 3. Reviewer role management & endpoint hardening

**Priority:** P2
**Labels:** `backend`, `security`, `reviewer`

**Description**
v0 uses a single `is_staff` flag for reviewer access with no rate limiting and no
audit view (`docs/threat-model.md`, Attack 5: a compromised reviewer account can
approve work and issue certificates). Introduce clearer reviewer roles and basic
abuse resistance — **without** building a full permissions system or external
identity verification.

**Acceptance criteria**
- [ ] A dedicated reviewer role/group (not just `is_staff`) gates reviewer routes,
      with a documented way to grant it.
- [ ] Rate limiting (throttling) on decision and certificate-issuance endpoints.
- [ ] An audit view/endpoint listing review decisions and certificate issuances
      with actor and timestamp (data already lives in the event chain).
- [ ] Tests: non-reviewers are rejected (already partially covered); throttle
      triggers after the configured limit.
- [ ] Threat-model doc updated to reflect the reduced (not eliminated) risk.

---

## 4. Editor session & event-delivery hardening

**Priority:** P2
**Labels:** `frontend`, `ux`, `reliability`

**Description**
The editor (`frontend/src/pages/projects/[id]/write.tsx`) does not reliably end a
session on navigation/tab-close (a beacon can't carry the auth token), and events
are lost if a request fails or the user is briefly offline. Harden delivery and
session lifecycle so the recorded evidence is more complete and trustworthy.

**Acceptance criteria**
- [ ] Session reliably ends on navigation away / tab close (auth-carrying
      `keepalive` fetch or an explicit flush-on-unload path).
- [ ] Failed event POSTs are queued and retried (with backoff) instead of dropped;
      queue survives transient offline periods within the session.
- [ ] Debounce/coalesce `text_changed` so redundant no-op events are not sent.
- [ ] User-visible indication of unsaved vs. saved evidence state.
- [ ] Manual test notes or a lightweight test covering the retry/flush path.

---

## 5. Reviewer evidence visualization

**Priority:** P3
**Labels:** `frontend`, `reviewer`, `ux`

**Description**
Reviewers currently see a raw event table and summary counts. Give them a
drafting-timeline view (paste ratio, typing bursts, session gaps, checkpoint
cadence) so decisions are faster and more consistent. This is presentation of
already-recorded evidence only — **no AI detection, no scoring that implies an
origin verdict.**

**Acceptance criteria**
- [ ] Reviewer detail page renders a timeline/summary derived from existing
      events (sessions, text_changed, checkpoints, pastes).
- [ ] Surfaces paste ratio (pasted characters vs. total), session count/durations,
      and gaps between activity.
- [ ] Clearly framed as descriptive evidence, not an automated judgment.
- [ ] No new backend event types required (compute from existing data); any new
      endpoint is read-only.

---

## Follow-up / smaller items (optional backlog)

- Restrict/replace `current_content` writes fully: it is now read-only via PATCH
  (done in the scaffold); consider removing it from the writable create payload
  path entirely and documenting the events-only content contract.
- Pagination for `GET /api/projects/{id}/events/` and the reviewer queue as event
  volume grows.
- Basic CI (run `pipenv run test`, `tsc --noEmit`, `npm run build` on PRs).
