import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/Layout";
import { EventLog, Project } from "@/lib/types";

// How often (ms) we flush accumulated typing as a single text_changed event.
// We deliberately do NOT record on every keystroke.
const TEXT_CHANGED_INTERVAL = 5000;
// Checkpoint cadence while the document is actively changing.
const CHECKPOINT_INTERVAL = 30000;

function wordCount(text: string): number {
  const t = text.trim();
  return t ? t.split(/\s+/).length : 0;
}

export default function WritePage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const projectId = router.query.id as string | undefined;

  const [project, setProject] = useState<Project | null>(null);
  const [content, setContent] = useState("");
  const [status, setStatus] = useState<string>("");
  const [pasteCount, setPasteCount] = useState(0);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  // Refs hold the "live" values our timers read without re-subscribing.
  const sessionIdRef = useRef<number | null>(null);
  const contentRef = useRef("");
  const lastTextChangedRef = useRef(""); // content at last text_changed flush
  const lastCheckpointRef = useRef(""); // content at last checkpoint

  contentRef.current = content;

  const post = useCallback(
    async (event_type: string, payload: Record<string, any>) => {
      if (!projectId) return;
      return api<EventLog>(`/projects/${projectId}/events/`, {
        method: "POST",
        body: {
          event_type,
          payload,
          session: sessionIdRef.current,
          content: contentRef.current,
        },
      });
    },
    [projectId]
  );

  const refreshEvidence = useCallback(async () => {
    if (!projectId) return;
    const [proj, ev] = await Promise.all([
      api<Project>(`/projects/${projectId}/`),
      api<{ events: EventLog[] }>(`/projects/${projectId}/events/`),
    ]);
    setProject(proj);
    setPasteCount(
      ev.events.filter((e) => e.event_type === "paste_detected").length
    );
  }, [projectId]);

  // On load: fetch the project, then start a drafting session.
  useEffect(() => {
    if (!ready || !projectId) return;
    let cancelled = false;

    (async () => {
      try {
        const proj = await api<Project>(`/projects/${projectId}/`);
        if (cancelled) return;
        setProject(proj);
        setContent(proj.current_content);
        lastTextChangedRef.current = proj.current_content;
        lastCheckpointRef.current = proj.current_content;

        const session = await api<{ id: number }>(
          `/projects/${projectId}/start-session/`,
          {
            method: "POST",
            body: {
              client_info: {
                user_agent:
                  typeof navigator !== "undefined" ? navigator.userAgent : "",
              },
            },
          }
        );
        if (cancelled) return;
        sessionIdRef.current = session.id;
        setStatus("Session started");
        refreshEvidence();
      } catch (e: any) {
        setError(e.message);
      }
    })();

    // Note: the reliable way to end a session is the visible "End session" /
    // "Submit" buttons. We don't try to end it on tab close because a beacon
    // can't carry the auth header; the backend tolerates open sessions.
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, projectId]);

  // Periodic text_changed flush.
  useEffect(() => {
    if (!ready) return;
    const t = setInterval(async () => {
      if (contentRef.current !== lastTextChangedRef.current) {
        const snapshot = contentRef.current;
        try {
          await post("text_changed", { word_count: wordCount(snapshot) });
          lastTextChangedRef.current = snapshot;
          setStatus(`Saved at ${new Date().toLocaleTimeString()}`);
          refreshEvidence();
        } catch (e: any) {
          setError(e.message);
        }
      }
    }, TEXT_CHANGED_INTERVAL);
    return () => clearInterval(t);
  }, [ready, post, refreshEvidence]);

  // Checkpoint every 30s while the document is actively changing.
  useEffect(() => {
    if (!ready) return;
    const t = setInterval(async () => {
      if (contentRef.current !== lastCheckpointRef.current) {
        const snapshot = contentRef.current;
        try {
          await post("checkpoint_created", {
            word_count: wordCount(snapshot),
            character_count: snapshot.length,
          });
          lastCheckpointRef.current = snapshot;
          setStatus(`Checkpoint at ${new Date().toLocaleTimeString()}`);
          refreshEvidence();
        } catch (e: any) {
          setError(e.message);
        }
      }
    }, CHECKPOINT_INTERVAL);
    return () => clearInterval(t);
  }, [ready, post, refreshEvidence]);

  function onPaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const pasted = e.clipboardData.getData("text");
    // Record the paste as evidence. We do not block pasting — we witness it.
    post("paste_detected", {
      character_count: pasted.length,
      word_count: wordCount(pasted),
      timestamp: new Date().toISOString(),
    })
      .then(() => refreshEvidence())
      .catch((err) => setError(err.message));
  }

  async function endSession() {
    if (!sessionIdRef.current || !projectId) return;
    try {
      // Flush any pending text before ending.
      if (contentRef.current !== lastTextChangedRef.current) {
        await post("text_changed", { word_count: wordCount(contentRef.current) });
        lastTextChangedRef.current = contentRef.current;
      }
      await api(`/projects/${projectId}/end-session/`, {
        method: "POST",
        body: { session: sessionIdRef.current },
      });
      sessionIdRef.current = null;
      setStatus("Session ended");
      refreshEvidence();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function submitForReview() {
    if (!projectId) return;
    setSaving(true);
    try {
      await endSession();
      await api(`/projects/${projectId}/submit/`, { method: "POST" });
      router.push(`/projects/${projectId}/history`);
    } catch (e: any) {
      setError(e.message);
      setSaving(false);
    }
  }

  if (!ready) return null;

  return (
    <div>
      <div className="row">
        <h1>{project?.title || "Loading…"}</h1>
        {project && <span className={`badge ${project.status}`}>{project.status}</span>}
        <span className="spacer" style={{ flex: 1 }} />
        <Link href={`/projects/${projectId}/history`}>History</Link>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="grid-2">
        <div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onPaste={onPaste}
            rows={22}
            placeholder="Start writing here. DraftWitness records your drafting process."
            style={{ resize: "vertical" }}
          />
          <p className="muted" style={{ minHeight: 20 }}>
            {status}
          </p>
          <div className="row">
            <button className="secondary" onClick={endSession}>
              End session
            </button>
            <button onClick={submitForReview} disabled={saving}>
              {saving ? "Submitting…" : "Submit for review"}
            </button>
          </div>
        </div>

        <aside className="panel">
          <h2>Certification evidence</h2>
          <div className="stat">
            <span>Word count</span>
            <strong>{wordCount(content)}</strong>
          </div>
          <div className="stat">
            <span>Sessions</span>
            <strong>{project?.session_count ?? 0}</strong>
          </div>
          <div className="stat">
            <span>Events</span>
            <strong>{project?.event_count ?? 0}</strong>
          </div>
          <div className="stat">
            <span>Paste events</span>
            <strong>{pasteCount}</strong>
          </div>
          <div style={{ marginTop: 12 }}>
            <div className="muted">Latest document hash</div>
            <div className="mono">{project?.current_hash || "—"}</div>
          </div>
          <p className="disclaimer">
            DraftWitness records your writing process. It verifies the recorded
            workflow — not metaphysical certainty about all possible activity.
          </p>
        </aside>
      </div>
    </div>
  );
}
