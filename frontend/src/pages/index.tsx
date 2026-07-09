import Link from "next/link";

export default function Home() {
  return (
    <div>
      <h1>Human-Origin Verified writing</h1>
      <p className="muted">
        DraftWitness is a monitored writing workflow. It records your drafting
        events, builds a tamper-evident history, and — after human review —
        issues a public certificate of <strong>Witnessed Human-Origin
        Drafting</strong>.
      </p>

      <div className="card">
        <h2>What DraftWitness verifies</h2>
        <p>
          DraftWitness certifies that a work was created through its recorded
          drafting workflow: the sessions, edits, and checkpoints captured
          inside the system. This is a <em>process</em> verification.
        </p>
        <p className="muted">
          It is not a claim of absolute certainty about all activity outside the
          recorded workflow, and it does not attempt to &ldquo;detect AI.&rdquo;
        </p>
      </div>

      <div className="row">
        <Link className="button" href="/register">
          Get started
        </Link>
        <Link className="button secondary" href="/login">
          Log in
        </Link>
      </div>
    </div>
  );
}
