"""Data model for DraftWitness.

DraftWitness records a monitored writing workflow. The tamper-evident spine is the
EventLog hash chain (see hashchain.py); everything else hangs off Project.
"""
import secrets
import string

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from .hashchain import compute_event_hash


class Project(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_APPROVED = "approved"
    STATUS_DENIED = "denied"
    STATUS_INCONCLUSIVE = "inconclusive"
    STATUS_CERTIFIED = "certified"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
        (STATUS_INCONCLUSIVE, "Inconclusive"),
        (STATUS_CERTIFIED, "Certified"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField(max_length=255)
    current_content = models.TextField(blank=True, default="")
    # Convenience mirror of the latest event_hash for the project's content.
    current_hash = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class DraftSession(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="sessions"
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    client_info = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["started_at", "id"]

    def __str__(self):
        return f"Session {self.id} for project {self.project_id}"


class EventLogManager(models.Manager):
    @transaction.atomic
    def append_event(self, *, project, event_type, payload=None, session=None):
        """Append a new event to the project's hash chain.

        This is the ONLY supported way to create an EventLog. It:
          1. locks the project row so concurrent appends can't fork the chain,
          2. reads the current tail (latest event_hash) as previous_hash,
          3. computes this event's hash over its canonical fields, and
          4. mirrors the new hash onto Project.current_hash.
        """
        payload = payload or {}

        # Lock the project so two simultaneous appends serialize; otherwise
        # both could read the same previous_hash and break the chain.
        locked_project = (
            Project.objects.select_for_update().get(pk=project.pk)
        )

        last_event = (
            self.filter(project=locked_project)
            .order_by("-created_at", "-id")
            .first()
        )
        previous_hash = last_event.event_hash if last_event else ""

        # Freeze the timestamp string that goes into the hash so verification
        # never depends on how the database round-trips datetimes.
        created_at = timezone.now()
        created_at_iso = created_at.isoformat()

        event_hash = compute_event_hash(
            project_id=locked_project.id,
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            created_at=created_at_iso,
        )

        event = self.create(
            project=locked_project,
            session=session,
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            event_hash=event_hash,
            created_at=created_at,
            created_at_iso=created_at_iso,
        )

        # Keep the project's convenience mirror in sync.
        locked_project.current_hash = event_hash
        locked_project.save(update_fields=["current_hash", "updated_at"])

        return event


class EventLog(models.Model):
    SESSION_STARTED = "session_started"
    TEXT_CHANGED = "text_changed"
    PASTE_DETECTED = "paste_detected"
    CHECKPOINT_CREATED = "checkpoint_created"
    SESSION_ENDED = "session_ended"
    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    REVIEW_DECISION = "review_decision"
    CERTIFICATE_ISSUED = "certificate_issued"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="events"
    )
    session = models.ForeignKey(
        DraftSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True, default="")
    event_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now)
    # The exact ISO string that was fed into the hash. Stored so verification
    # is independent of database datetime precision/round-tripping.
    created_at_iso = models.CharField(max_length=64, blank=True, default="")

    objects = EventLogManager()

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.event_type} @ {self.event_hash[:12]}"


class ReviewDecision(models.Model):
    DECISION_APPROVED = "approved"
    DECISION_DENIED = "denied"
    DECISION_INCONCLUSIVE = "inconclusive"
    DECISION_CHOICES = [
        (DECISION_APPROVED, "Approved"),
        (DECISION_DENIED, "Denied"),
        (DECISION_INCONCLUSIVE, "Inconclusive"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="decisions"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_decisions",
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.decision} on project {self.project_id}"


def generate_certificate_id() -> str:
    """Human-readable, unique-ish certificate id like DW-2026-ABC123."""
    year = timezone.now().year
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"DW-{year}-{suffix}"


class Certificate(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVOKED, "Revoked"),
    ]

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="certificate"
    )
    certificate_id = models.CharField(max_length=32, unique=True)
    certification_level = models.CharField(
        max_length=64, default="Human-Origin Verified"
    )
    final_document_hash = models.CharField(max_length=64, blank=True, default="")
    evidence_summary = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.certificate_id} ({self.status})"
