"""Tamper-evident hash chaining for DraftWitness event logs.

The core promise of DraftWitness is a *tamper-evident* history of drafting
events. We achieve this with a simple hash chain (the same idea a blockchain
uses internally, minus the distributed consensus — we deliberately do NOT add
a blockchain here).

Each event stores:
  * previous_hash: the event_hash of the immediately preceding event for the
    same project (empty string for the very first event).
  * event_hash: SHA-256 over a canonical JSON encoding of the event's core
    fields, INCLUDING previous_hash.

Because each hash commits to the previous hash, editing any historical event
(e.g. tampering with a payload directly in the database) changes that event's
hash, which no longer matches the previous_hash recorded in the next event.
`verify_project_chain` walks the chain and detects exactly this.
"""
import hashlib
import json


def canonical_json(data) -> str:
    """Serialize ``data`` to a deterministic JSON string.

    Determinism matters: the same logical event must always produce the same
    bytes, or the hash would be unstable. We sort keys and use compact,
    ASCII-safe separators so the encoding never depends on dict ordering or
    incidental whitespace.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def compute_event_hash(
    *,
    project_id,
    event_type: str,
    payload,
    previous_hash: str,
    created_at: str,
) -> str:
    """Return the SHA-256 hex digest for a single event.

    The hashed document intentionally contains everything that defines the
    event's meaning and position in the chain. Changing any of these fields
    changes the hash.
    """
    document = {
        "project_id": project_id,
        "event_type": event_type,
        "payload": payload,
        "previous_hash": previous_hash,
        "created_at": created_at,
    }
    encoded = canonical_json(document).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_project_chain(project) -> dict:
    """Verify the integrity of a project's full event chain.

    Returns a dict:
        {
            "valid": bool,
            "event_count": int,
            "broken_at": <event id or None>,
            "reason": <str or None>,
        }

    We recompute each event's hash from its stored fields and confirm:
      1. previous_hash links to the prior event's event_hash (or "" for the
         first event), and
      2. the stored event_hash matches a fresh recomputation (catching payload
         tampering).
    """
    # Import locally to avoid a circular import at module load time.
    from .models import EventLog

    events = list(
        EventLog.objects.filter(project=project).order_by("created_at", "id")
    )

    expected_previous = ""
    for event in events:
        # (1) The chain link must point at the previous event's hash.
        if event.previous_hash != expected_previous:
            return {
                "valid": False,
                "event_count": len(events),
                "broken_at": event.id,
                "reason": "previous_hash does not match prior event's event_hash",
            }

        # (2) Recompute the hash from stored fields; tampering shows up here.
        recomputed = compute_event_hash(
            project_id=event.project_id,
            event_type=event.event_type,
            payload=event.payload,
            previous_hash=event.previous_hash,
            created_at=event.created_at_iso,
        )
        if recomputed != event.event_hash:
            return {
                "valid": False,
                "event_count": len(events),
                "broken_at": event.id,
                "reason": "event_hash does not match recomputed hash (payload tampered?)",
            }

        expected_previous = event.event_hash

    return {
        "valid": True,
        "event_count": len(events),
        "broken_at": None,
        "reason": None,
    }
