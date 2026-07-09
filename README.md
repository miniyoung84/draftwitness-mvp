# DraftWitness

**Human-origin certification for written creative work.**

DraftWitness is a monitored writing workflow. It records drafting events inside
its own editor, stores them in a **tamper-evident, hash-chained** event log,
lets a human reviewer approve the work, and issues a **public certificate** with
an evidence summary.

DraftWitness does **not** "detect AI" and makes **no** "AI-free guaranteed"
claim. It verifies the *creation process recorded inside the system* —
**Witnessed Human-Origin Drafting** — not metaphysical certainty about all
possible AI use. See [`docs/product-spec.md`](docs/product-spec.md),
[`docs/certification-standard.md`](docs/certification-standard.md), and
[`docs/threat-model.md`](docs/threat-model.md).

## Repository structure

```
draftwitness-mvp/
  backend/     Django + DRF API (hash-chained event log, review, certificates)
  frontend/    Next.js + TypeScript app (editor, dashboard, review, certificates)
  docs/        Product spec, certification standard, threat model
  README.md
```

## Stack

- **Backend:** Django 5, Django REST Framework, token auth. PostgreSQL in
  production; SQLite by default for local development (zero setup).
- **Frontend:** Next.js 14 (pages router) + TypeScript, minimal hand-rolled CSS.
- **Dependency management:** `pipenv` for the backend, `npm` for the frontend.

## Local setup

### 1. Backend

Requires Python 3.12 and `pipenv` (`pip install pipenv`).

```bash
cd backend
cp .env.example .env            # SQLite works out of the box; edit for Postgres
pipenv install                  # create the venv and install deps
pipenv run migrate              # apply migrations
pipenv run seed                 # optional: demo users + a sample project
pipenv run server               # http://localhost:8000
```

Create a reviewer (staff) account so you can access the review pages:

```bash
pipenv run python manage.py createsuperuser
```

Any user with `is_staff = True` is treated as a reviewer. The `seed` command
also creates a ready-made reviewer (`reviewer` / `reviewer12345`) and writer
(`writer` / `writer12345`).

**Backend commands** (defined as Pipfile scripts):

| Command | Does |
| --- | --- |
| `pipenv run server` | Run the dev server on :8000 |
| `pipenv run migrate` | Apply database migrations |
| `pipenv run makemigrations` | Generate migrations after model changes |
| `pipenv run test` | Run the test suite |
| `pipenv run seed` | Seed demo users and a sample project |

### 2. Frontend

Requires Node 18+.

```bash
cd frontend
cp .env.example .env.local      # points at http://localhost:8000/api
npm install
npm run dev                     # http://localhost:3000
```

**Frontend commands:** `npm run dev`, `npm run build`, `npm run start`.

### Using PostgreSQL instead of SQLite

Set either `DATABASE_URL=postgres://user:pass@host:5432/dbname` or the discrete
`POSTGRES_*` variables in `backend/.env`, then run `pipenv run migrate`. If
neither is set, DraftWitness falls back to a local `db.sqlite3` file.

## Running the tests

```bash
cd backend
pipenv run test
```

The test suite focuses on the **hash-chain / event-log** behavior
(`backend/api/tests.py`): events are chained in order, an untampered project
verifies, and tampering with any event payload (or hash) breaks verification.

## Demo flow

1. Start the backend (`pipenv run server`) and frontend (`npm run dev`).
2. Register a user at http://localhost:3000/register (or log in as the seeded
   `writer` / `writer12345`).
3. Create a project (`/projects/new`) and write in the editor. Watch the
   **Certification evidence** panel update: word count, sessions, events, paste
   events, and the latest document hash. Try pasting text — it's recorded as a
   `paste_detected` event.
4. Click **Submit for review**.
5. Log in as a reviewer (`reviewer` / `reviewer12345`, or your superuser) and go
   to **Review**. Open the submitted project, inspect the event history and
   evidence, then **Approve** it and **Issue certificate**.
6. Open the public certificate page at
   `/certificates/<certificate_id>` (e.g. `DW-2026-ABC123`) — this page is
   public and shows the status, evidence summary, and disclaimer.

## How the hash chain works (the core idea)

Each `EventLog` row stores `event_hash = SHA-256(canonical_json({project_id,
event_type, payload, previous_hash, created_at}))`, where `previous_hash` is the
prior event's hash (empty string for the first event). Because every hash commits
to the previous one, editing any historical event changes its hash and no longer
matches the next event's `previous_hash`. `verify_project_chain` walks the chain
and detects exactly this. See `backend/api/hashchain.py` (heavily commented).

There is **no blockchain**, no AI detection, no payments, and no marketplace —
by design for this MVP.
