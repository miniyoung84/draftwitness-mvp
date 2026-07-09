import { useRouter } from "next/router";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/Layout";
import { Project } from "@/lib/types";

export default function NewProject() {
  const ready = useRequireAuth();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!ready) return null;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const project = await api<Project>("/projects/", {
        method: "POST",
        body: { title },
      });
      router.push(`/projects/${project.id}/write`);
    } catch (err: any) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 480 }}>
      <h1>New writing project</h1>
      <form onSubmit={submit}>
        <label>Title</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Working title"
          required
        />
        {error && <p className="error">{error}</p>}
        <p>
          <button disabled={busy} type="submit">
            {busy ? "Creating…" : "Create & start writing"}
          </button>
        </p>
      </form>
    </div>
  );
}
