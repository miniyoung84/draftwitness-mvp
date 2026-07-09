// Shared shapes mirroring the backend serializers.
export interface Project {
  id: number;
  title: string;
  current_content: string;
  current_hash: string;
  status:
    | "draft"
    | "submitted"
    | "approved"
    | "denied"
    | "inconclusive"
    | "certified";
  event_count: number;
  session_count: number;
  created_at: string;
  updated_at: string;
  owner_username?: string;
}

export interface EventLog {
  id: number;
  session: number | null;
  event_type: string;
  payload: Record<string, any>;
  previous_hash: string;
  event_hash: string;
  created_at: string;
}

export interface Verification {
  valid: boolean;
  event_count: number;
  broken_at: number | null;
  reason: string | null;
}

export interface EvidenceSummary {
  word_count: number;
  session_count: number;
  event_count: number;
  paste_event_count: number;
  pasted_characters: number;
  latest_document_hash: string;
}

export interface Certificate {
  certificate_id: string;
  title: string;
  certification_level: string;
  final_document_hash: string;
  evidence_summary: EvidenceSummary;
  status: "active" | "revoked";
  issued_at: string;
  revoked_at: string | null;
}
