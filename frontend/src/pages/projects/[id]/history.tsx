import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/Layout";
import { EventLog, Project, Verification } from "@/lib/types";

export default function HistoryPage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const projectId = router.query.id as string | undefined;

  const [project, setProject] = useState<Project | null>(null);
  const [events, setEvents] = useState<EventLog[]>([]);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready || !projectId) return;
    Promise.all([
      api<Project>(`/projects/${projectId}/`),
      api<{ events: EventLog[]; verification: Verification }>(
        `/projects/${projectId}/events/`
      ),
    ])
      .then(([proj, ev]) => {
        setProject(proj);
        setEvents(ev.events);
        setVerification(ev.verification);
      })
      .catch((e) => setError(e.message));
  }, [ready, projectId]);

  if (!ready) return null;

  return (
    <div>
      <div className="row">
        <h1>{project?.title || "History"}</h1>
        {project && <span className={`badge ${project.status}`}>{project.status}</span>}
        <span className="spacer" style={{ flex: 1 }} />
        <Link href={`/projects/${projectId}/write`}>Back to editor</Link>
      </div>

      {error && <p className="error">{error}</p>}

      {verification && (
        <div className="panel" style={{ marginBottom: 16 }}>
          <strong>Chain verification: </strong>
          {verification.valid ? (
            <span className="badge approved">valid</span>
          ) : (
            <span className="badge denied">broken</span>
          )}
          <span className="muted">
            {" "}
            · {verification.event_count} events
            {verification.reason ? ` · ${verification.reason}` : ""}
          </span>
        </div>
      )}

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Event</th>
            <th>When</th>
            <th>Details</th>
            <th>Hash</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e, i) => (
            <tr key={e.id}>
              <td>{i + 1}</td>
              <td>{e.event_type}</td>
              <td>{new Date(e.created_at).toLocaleTimeString()}</td>
              <td className="muted">
                {Object.keys(e.payload).length
                  ? JSON.stringify(e.payload)
                  : "—"}
              </td>
              <td className="mono">{e.event_hash.slice(0, 12)}…</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
