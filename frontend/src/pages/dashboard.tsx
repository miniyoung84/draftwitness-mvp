import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/Layout";
import { Project } from "@/lib/types";

export default function Dashboard() {
  const ready = useRequireAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready) return;
    api<Project[]>("/projects/")
      .then(setProjects)
      .catch((e) => setError(e.message));
  }, [ready]);

  if (!ready) return null;

  return (
    <div>
      <div className="row">
        <h1>Your projects</h1>
        <span className="spacer" style={{ flex: 1 }} />
        <Link className="button" href="/projects/new">
          + New project
        </Link>
      </div>

      {error && <p className="error">{error}</p>}
      {projects.length === 0 && (
        <p className="muted">No projects yet. Create your first one.</p>
      )}

      {projects.map((p) => (
        <div className="card" key={p.id}>
          <div className="row">
            <strong>{p.title}</strong>
            <span className={`badge ${p.status}`}>{p.status}</span>
            <span className="spacer" style={{ flex: 1 }} />
            <Link href={`/projects/${p.id}/write`}>Write</Link>
            <Link href={`/projects/${p.id}/history`}>History</Link>
          </div>
          <p className="muted" style={{ margin: "8px 0 0" }}>
            {p.event_count} events · {p.session_count} sessions · updated{" "}
            {new Date(p.updated_at).toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}
