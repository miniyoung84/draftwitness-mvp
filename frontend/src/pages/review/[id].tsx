import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/Layout";
import {
  Certificate,
  EventLog,
  EvidenceSummary,
  Project,
  Verification,
} from "@/lib/types";

interface ReviewerDetail extends Project {
  events: EventLog[];
  verification: Verification;
  evidence_summary: EvidenceSummary;
  decisions: { id: number; decision: string; notes: string; created_at: string }[];
  certificate?: Certificate;
}

export default function ReviewDetail() {
  const ready = useRequireAuth();
  const router = useRouter();
  const projectId = router.query.id as string | undefined;

  const [data, setData] = useState<ReviewerDetail | null>(null);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    if (!projectId) return;
    api<ReviewerDetail>(`/reviewer/projects/${projectId}/`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [projectId]);

  useEffect(() => {
    if (!ready) return;
    load();
  }, [ready, load]);

  async function decide(decision: string) {
    if (!projectId) return;
    setBusy(true);
    setError("");
    try {
      await api(`/reviewer/projects/${projectId}/decision/`, {
        method: "POST",
        body: { decision, notes },
      });
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function issueCertificate() {
    if (!projectId) return;
    setBusy(true);
    setError("");
    try {
      await api(`/reviewer/projects/${projectId}/issue-certificate/`, {
        method: "POST",
      });
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!ready) return null;
  if (!data) return <p className="muted">{error || "Loading…"}</p>;

  const ev = data.evidence_summary;

  return (
    <div>
      <div className="row">
        <h1>{data.title}</h1>
        <span className={`badge ${data.status}`}>{data.status}</span>
        <span className="spacer" style={{ flex: 1 }} />
        <Link href="/review">← Queue</Link>
      </div>
      <p className="muted">by {data.owner_username}</p>

      {error && <p className="error">{error}</p>}

      <div className="grid-2">
        <div>
          <div className="card">
            <h2>Submitted work</h2>
            <p style={{ whiteSpace: "pre-wrap" }}>{data.current_content}</p>
          </div>

          <div className="card">
            <h2>Event history ({data.events.length})</h2>
            <div className="panel" style={{ marginBottom: 12 }}>
              <strong>Chain: </strong>
              {data.verification.valid ? (
                <span className="badge approved">valid</span>
              ) : (
                <span className="badge denied">broken</span>
              )}
            </div>
            <table>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>When</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {data.events.map((e) => (
                  <tr key={e.id}>
                    <td>{e.event_type}</td>
                    <td>{new Date(e.created_at).toLocaleTimeString()}</td>
                    <td className="muted">
                      {Object.keys(e.payload).length
                        ? JSON.stringify(e.payload)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <aside>
          <div className="panel">
            <h2>Evidence summary</h2>
            <div className="stat">
              <span>Words</span>
              <strong>{ev.word_count}</strong>
            </div>
            <div className="stat">
              <span>Sessions</span>
              <strong>{ev.session_count}</strong>
            </div>
            <div className="stat">
              <span>Events</span>
              <strong>{ev.event_count}</strong>
            </div>
            <div className="stat">
              <span>Paste events</span>
              <strong>{ev.paste_event_count}</strong>
            </div>
            <div className="stat">
              <span>Pasted characters</span>
              <strong>{ev.pasted_characters}</strong>
            </div>
            <div style={{ marginTop: 10 }}>
              <div className="muted">Final document hash</div>
              <div className="mono">{ev.latest_document_hash || "—"}</div>
            </div>
          </div>

          <div className="card">
            <h2>Decision</h2>
            <label>Notes</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Reviewer notes (optional)"
            />
            <div className="row" style={{ marginTop: 10, flexWrap: "wrap" }}>
              <button disabled={busy} onClick={() => decide("approved")}>
                Approve
              </button>
              <button
                className="secondary"
                disabled={busy}
                onClick={() => decide("inconclusive")}
              >
                Inconclusive
              </button>
              <button
                className="secondary"
                disabled={busy}
                onClick={() => decide("denied")}
              >
                Deny
              </button>
            </div>

            {data.status === "approved" && !data.certificate && (
              <p style={{ marginTop: 14 }}>
                <button disabled={busy} onClick={issueCertificate}>
                  Issue certificate
                </button>
              </p>
            )}

            {data.certificate && (
              <p style={{ marginTop: 14 }}>
                Certificate issued:{" "}
                <Link href={`/certificates/${data.certificate.certificate_id}`}>
                  {data.certificate.certificate_id}
                </Link>
              </p>
            )}
          </div>

          {data.decisions.length > 0 && (
            <div className="card">
              <h2>Decision history</h2>
              {data.decisions.map((d) => (
                <div key={d.id} className="stat">
                  <span className={`badge ${d.decision}`}>{d.decision}</span>
                  <span className="muted">
                    {new Date(d.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
