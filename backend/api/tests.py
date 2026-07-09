"""Tests for the tamper-evident event hash chain — the heart of DraftWitness."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .hashchain import compute_event_hash, verify_project_chain
from .models import Certificate, EventLog, Project

User = get_user_model()


class HashChainTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="writer", password="pw12345678")
        self.project = Project.objects.create(owner=self.user, title="My Story")

    def _append(self, event_type, payload):
        return EventLog.objects.append_event(
            project=self.project, event_type=event_type, payload=payload
        )

    def test_events_are_chained_in_order(self):
        """Each event's previous_hash must equal the prior event's event_hash."""
        e1 = self._append(EventLog.SESSION_STARTED, {"session_id": 1})
        e2 = self._append(EventLog.TEXT_CHANGED, {"length": 10})
        e3 = self._append(EventLog.CHECKPOINT_CREATED, {"n": 1})

        # First event links to the empty string (genesis).
        self.assertEqual(e1.previous_hash, "")
        # Subsequent events link to the immediately preceding hash.
        self.assertEqual(e2.previous_hash, e1.event_hash)
        self.assertEqual(e3.previous_hash, e2.event_hash)
        # The project mirror tracks the latest hash.
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_hash, e3.event_hash)

    def test_untampered_project_verifies(self):
        self._append(EventLog.SESSION_STARTED, {"session_id": 1})
        self._append(EventLog.TEXT_CHANGED, {"length": 42})
        self._append(EventLog.SESSION_ENDED, {"session_id": 1})

        result = verify_project_chain(self.project)
        self.assertTrue(result["valid"])
        self.assertIsNone(result["broken_at"])
        self.assertEqual(result["event_count"], 3)

    def test_tampering_with_payload_breaks_verification(self):
        self._append(EventLog.SESSION_STARTED, {"session_id": 1})
        tampered = self._append(EventLog.TEXT_CHANGED, {"length": 42})
        self._append(EventLog.SESSION_ENDED, {"session_id": 1})

        # Simulate someone editing a payload directly in the database. The
        # stored event_hash no longer matches the recomputed hash.
        tampered.payload = {"length": 999999}
        tampered.save(update_fields=["payload"])

        result = verify_project_chain(self.project)
        self.assertFalse(result["valid"])
        self.assertEqual(result["broken_at"], tampered.id)

    def test_tampering_with_event_hash_breaks_chain_link(self):
        e1 = self._append(EventLog.SESSION_STARTED, {"session_id": 1})
        self._append(EventLog.TEXT_CHANGED, {"length": 42})

        # Corrupt the first event's stored hash; the second event's
        # previous_hash no longer matches, so the chain link is broken.
        e1.event_hash = "0" * 64
        e1.save(update_fields=["event_hash"])

        result = verify_project_chain(self.project)
        self.assertFalse(result["valid"])

    def test_hash_is_deterministic(self):
        """The same logical event always produces the same hash."""
        args = dict(
            project_id=1,
            event_type=EventLog.TEXT_CHANGED,
            payload={"b": 2, "a": 1},
            previous_hash="",
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual(compute_event_hash(**args), compute_event_hash(**args))

    def test_empty_project_verifies(self):
        result = verify_project_chain(self.project)
        self.assertTrue(result["valid"])
        self.assertEqual(result["event_count"], 0)


class ApiFlowTests(TestCase):
    """End-to-end walk through the full certification workflow via the API."""

    def setUp(self):
        self.client = APIClient()
        self.reviewer = User.objects.create_user(
            username="reviewer", password="pw12345678", is_staff=True
        )

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_full_workflow(self):
        # 1. Register a writer -> get a token.
        res = self.client.post(
            "/api/auth/register/",
            {"username": "author", "password": "pw12345678"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        writer_token = res.data["token"]
        self._auth(writer_token)

        # 2. Create a project.
        res = self.client.post(
            "/api/projects/", {"title": "My Novel"}, format="json"
        )
        self.assertEqual(res.status_code, 201, res.content)
        project_id = res.data["id"]

        # 3. Start a session, append events (incl. a paste), end the session.
        res = self.client.post(
            f"/api/projects/{project_id}/start-session/",
            {"client_info": {"ua": "test"}},
            format="json",
        )
        session_id = res.data["id"]

        self.client.post(
            f"/api/projects/{project_id}/events/",
            {
                "event_type": "text_changed",
                "payload": {"word_count": 3},
                "session": session_id,
                "content": "Once upon time",
            },
            format="json",
        )
        self.client.post(
            f"/api/projects/{project_id}/events/",
            {
                "event_type": "paste_detected",
                "payload": {"character_count": 20, "word_count": 4},
                "session": session_id,
            },
            format="json",
        )
        self.client.post(
            f"/api/projects/{project_id}/end-session/",
            {"session": session_id},
            format="json",
        )

        # Chain must verify through the API.
        res = self.client.get(f"/api/projects/{project_id}/events/")
        self.assertTrue(res.data["verification"]["valid"])

        # 4. Submit for review.
        res = self.client.post(f"/api/projects/{project_id}/submit/", format="json")
        self.assertEqual(res.data["status"], Project.STATUS_SUBMITTED)

        # 5. A non-reviewer cannot see the reviewer queue.
        res = self.client.get("/api/reviewer/projects/")
        self.assertEqual(res.status_code, 403)

        # 6. Reviewer approves and issues a certificate.
        res = self.client.post(
            "/api/auth/login/",
            {"username": "reviewer", "password": "pw12345678"},
            format="json",
        )
        self._auth(res.data["token"])

        res = self.client.get("/api/reviewer/projects/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

        res = self.client.post(
            f"/api/reviewer/projects/{project_id}/decision/",
            {"decision": "approved", "notes": "looks good"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)

        res = self.client.post(
            f"/api/reviewer/projects/{project_id}/issue-certificate/",
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        certificate_id = res.data["certificate_id"]
        self.assertTrue(certificate_id.startswith("DW-"))

        # 7. Public certificate is readable without auth.
        anon = APIClient()
        res = anon.get(f"/api/certificates/{certificate_id}/")
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.data["certification_level"], "Human-Origin Verified")
        self.assertEqual(res.data["evidence_summary"]["paste_event_count"], 1)
        self.assertEqual(res.data["status"], "active")

        # Project is now certified and still verifies.
        project = Project.objects.get(pk=project_id)
        self.assertEqual(project.status, Project.STATUS_CERTIFIED)
        self.assertTrue(verify_project_chain(project)["valid"])
        self.assertEqual(Certificate.objects.count(), 1)


class ProjectUpdateTests(TestCase):
    """PATCH may edit metadata (title) but never content; content flows only
    through the event endpoint, which keeps the hash chain authoritative."""

    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(username="author", password="pw12345678")
        self.project = Project.objects.create(
            owner=user, title="Original Title", current_content="original text"
        )
        # Authenticate as the owner.
        from rest_framework.authtoken.models import Token

        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_patch_can_update_title(self):
        res = self.client.patch(
            f"/api/projects/{self.project.id}/",
            {"title": "New Title"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "New Title")

    def test_patch_cannot_update_current_content(self):
        res = self.client.patch(
            f"/api/projects/{self.project.id}/",
            {"title": "Renamed", "current_content": "tampered directly"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.project.refresh_from_db()
        # Title still updates...
        self.assertEqual(self.project.title, "Renamed")
        # ...but the read-only content field is ignored, not applied.
        self.assertEqual(self.project.current_content, "original text")

    def test_patch_cannot_update_current_hash(self):
        res = self.client.patch(
            f"/api/projects/{self.project.id}/",
            {"current_hash": "deadbeef"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_hash, "")

    def test_content_changes_through_event_endpoint(self):
        """Posting an event updates content AND appends to the hash chain."""
        self.assertEqual(self.project.events.count(), 0)

        res = self.client.post(
            f"/api/projects/{self.project.id}/events/",
            {
                "event_type": "text_changed",
                "payload": {"word_count": 2},
                "content": "brand new content",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)

        self.project.refresh_from_db()
        # Content was updated via the event endpoint...
        self.assertEqual(self.project.current_content, "brand new content")
        # ...an event was chained...
        self.assertEqual(self.project.events.count(), 1)
        # ...and current_hash now mirrors the latest event hash.
        self.assertEqual(self.project.current_hash, res.data["event_hash"])
        self.assertTrue(verify_project_chain(self.project)["valid"])
