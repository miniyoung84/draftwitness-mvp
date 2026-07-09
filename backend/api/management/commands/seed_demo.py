"""Seed a demo world: a writer, a reviewer, and one drafted project.

Run with:  pipenv run seed   (or  python manage.py seed_demo)

Idempotent-ish: it creates users only if missing, and always appends a fresh
demo project so you can re-run it during development.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.evidence import build_evidence_summary
from api.models import DraftSession, EventLog, Project

User = get_user_model()

DEMO_TEXT = (
    "The lighthouse keeper wrote by hand every night, long after the last "
    "ship had passed. He believed the words mattered more when no one was "
    "watching."
)


class Command(BaseCommand):
    help = "Seed demo users and a sample drafted project."

    def handle(self, *args, **options):
        writer, created = User.objects.get_or_create(username="writer")
        if created:
            writer.set_password("writer12345")
            writer.save()
            self.stdout.write("Created user 'writer' (password: writer12345)")

        reviewer, created = User.objects.get_or_create(
            username="reviewer", defaults={"is_staff": True}
        )
        if created:
            reviewer.set_password("reviewer12345")
            reviewer.is_staff = True
            reviewer.save()
            self.stdout.write(
                "Created reviewer 'reviewer' (password: reviewer12345)"
            )

        project = Project.objects.create(owner=writer, title="The Lighthouse Keeper")
        session = DraftSession.objects.create(project=project, client_info={"demo": True})

        EventLog.objects.append_event(
            project=project,
            event_type=EventLog.SESSION_STARTED,
            payload={"session_id": session.id},
            session=session,
        )
        # Simulate incremental typing captured as periodic text_changed events.
        for i in range(1, 4):
            partial = " ".join(DEMO_TEXT.split()[: i * 8])
            project.current_content = partial
            project.save(update_fields=["current_content", "updated_at"])
            EventLog.objects.append_event(
                project=project,
                event_type=EventLog.TEXT_CHANGED,
                payload={"word_count": len(partial.split())},
                session=session,
            )
        project.current_content = DEMO_TEXT
        project.save(update_fields=["current_content", "updated_at"])
        EventLog.objects.append_event(
            project=project,
            event_type=EventLog.CHECKPOINT_CREATED,
            payload={"word_count": len(DEMO_TEXT.split())},
            session=session,
        )
        EventLog.objects.append_event(
            project=project,
            event_type=EventLog.SESSION_ENDED,
            payload={"session_id": session.id},
            session=session,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded project #{project.id} '{project.title}' with "
                f"{project.events.count()} events. "
                f"Evidence: {build_evidence_summary(project)}"
            )
        )
