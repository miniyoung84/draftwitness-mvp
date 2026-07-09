"""Build the plain-language evidence summary shown on certificates and in the
writing UI's evidence panel.

This is intentionally descriptive, not judgmental: we report *what the recorded
workflow contains*, never a verdict about whether text is "AI" or "human".
"""
from .models import EventLog


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def build_evidence_summary(project) -> dict:
    events = list(project.events.all())
    paste_events = [e for e in events if e.event_type == EventLog.PASTE_DETECTED]

    pasted_characters = 0
    for e in paste_events:
        try:
            pasted_characters += int(e.payload.get("character_count", 0) or 0)
        except (TypeError, ValueError):
            pass

    return {
        "word_count": word_count(project.current_content),
        "session_count": project.sessions.count(),
        "event_count": len(events),
        "paste_event_count": len(paste_events),
        "pasted_characters": pasted_characters,
        "latest_document_hash": project.current_hash,
    }
