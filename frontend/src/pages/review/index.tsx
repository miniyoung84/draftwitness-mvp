import Link from "next/link";
import { useEffect, useState } from "react";
import { api, getUser } from "@/lib/api";
import { useRequireAuth } from "@/lib/Layout";
import { Project } from "@/lib/types";

export default function ReviewQueue() {
  const ready = useRequireAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ready) return;
    if (!getUser()?.is_reviewer) {
      setError("You need reviewer access to view this page.");
      return;
    }
    api<Project[]>("/reviewer/projects/")
      .then(setProjects)
      .catch((e) => setError(e.message));
  }, [ready]);

  if (!ready) return null;

  return (
    <div>
      <h1>Review queue</h1>
      {error && <p className="error">{error}</p>}
      {!error && projects.length === 0 && (
        <p className="muted">Nothing submitted yet.</p>
      )}
      {projects.map((p) => (
        <div className="card" key={p.id}>
          <div className="row">
            <strong>{p.title}</strong>
            <span className={`badge ${p.status}`}>{p.status}</span>
            <span className="spacer" style={{ flex: 1 }} />
            <span className="muted">by {p.owner_username}</span>
            <Link href={`/review/${p.id}`}>Open</Link>
          </div>
        </div>
      ))}
    </div>
  );
}
