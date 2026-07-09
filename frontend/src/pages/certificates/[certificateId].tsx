import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Certificate } from "@/lib/types";

// Public, unauthenticated certificate page.
export default function CertificatePage() {
  const router = useRouter();
  const certificateId = router.query.certificateId as string | undefined;
  const [cert, setCert] = useState<Certificate | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!certificateId) return;
    // auth: false — anyone with the link can verify a certificate.
    api<Certificate>(`/certificates/${certificateId}/`, { auth: false })
      .then(setCert)
      .catch((e) => setError(e.message));
  }, [certificateId]);

  if (error) return <p className="error">{error}</p>;
  if (!cert) return <p className="muted">Loading…</p>;

  const ev = cert.evidence_summary;

  return (
    <div style={{ maxWidth: 640 }}>
      <p className="muted" style={{ letterSpacing: 1, textTransform: "uppercase" }}>
        DraftWitness Certificate
      </p>
      <div className="row">
        <h1 style={{ margin: 0 }}>{cert.title}</h1>
        <span className={`badge ${cert.status}`}>{cert.status}</span>
      </div>

      <div className="card">
        <dl className="dl">
          <dt>Certificate ID</dt>
          <dd className="mono">{cert.certificate_id}</dd>

          <dt>Certification level</dt>
          <dd>{cert.certification_level}</dd>

          <dt>Status</dt>
          <dd style={{ textTransform: "capitalize" }}>{cert.status}</dd>

          <dt>Issued</dt>
          <dd>{new Date(cert.issued_at).toLocaleString()}</dd>
          {cert.revoked_at && (
            <>
              <dt>Revoked</dt>
              <dd>{new Date(cert.revoked_at).toLocaleString()}</dd>
            </>
          )}
        </dl>
      </div>

      <div className="panel">
        <h2>Evidence summary</h2>
        <div className="stat">
          <span>Drafting sessions</span>
          <strong>{ev.session_count}</strong>
        </div>
        <div className="stat">
          <span>Event count</span>
          <strong>{ev.event_count}</strong>
        </div>
        <div className="stat">
          <span>Paste events</span>
          <strong>{ev.paste_event_count}</strong>
        </div>
        <div className="stat">
          <span>Word count</span>
          <strong>{ev.word_count}</strong>
        </div>
        <div style={{ marginTop: 12 }}>
          <div className="muted">Final document hash</div>
          <div className="mono">{cert.final_document_hash || "—"}</div>
        </div>
      </div>

      <p className="disclaimer">
        This certificate verifies that the work was created through
        DraftWitness&rsquo;s recorded drafting workflow. It is not a claim of
        absolute certainty about all activity outside the recorded workflow.
      </p>
    </div>
  );
}
