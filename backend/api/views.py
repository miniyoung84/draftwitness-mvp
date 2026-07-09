"""DraftWitness API views.

Normal-user endpoints operate only on the requesting user's own projects.
Reviewer endpoints are gated behind IsReviewer (is_staff) and are kept under a
separate /reviewer/ namespace to cleanly separate user vs. reviewer surfaces.
The public certificate endpoint is the only unauthenticated read.
"""
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .evidence import build_evidence_summary
from .hashchain import verify_project_chain
from .models import (
    Certificate,
    DraftSession,
    EventLog,
    Project,
    ReviewDecision,
    generate_certificate_id,
)
from .permissions import IsReviewer
from .serializers import (
    CertificateSerializer,
    DraftSessionSerializer,
    EventLogSerializer,
    LoginSerializer,
    ProjectSerializer,
    RegisterSerializer,
    ReviewDecisionSerializer,
)

# Event types a client is allowed to append directly. Lifecycle events
# (submitted_for_review, review_decision, certificate_issued) are appended by
# the server only, never trusted from the client.
CLIENT_EVENT_TYPES = {
    EventLog.SESSION_STARTED,
    EventLog.TEXT_CHANGED,
    EventLog.PASTE_DETECTED,
    EventLog.CHECKPOINT_CREATED,
    EventLog.SESSION_ENDED,
}


def _token_response(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "user": {
            "id": user.id,
            "username": user.username,
            "is_reviewer": user.is_staff,
        },
    }


# --- Auth ---------------------------------------------------------------


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(_token_response(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(_token_response(user))


# --- Projects (owner-scoped) -------------------------------------------


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def projects(request):
    if request.method == "POST":
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(owner=request.user)
        return Response(
            ProjectSerializer(project).data, status=status.HTTP_201_CREATED
        )

    qs = Project.objects.filter(owner=request.user)
    return Response(ProjectSerializer(qs, many=True).data)


def _get_owned_project(request, pk):
    return get_object_or_404(Project, pk=pk, owner=request.user)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def project_detail(request, pk):
    project = _get_owned_project(request, pk)

    if request.method == "PATCH":
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProjectSerializer(project).data)

    return Response(ProjectSerializer(project).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def project_events(request, pk):
    project = _get_owned_project(request, pk)

    if request.method == "GET":
        events = project.events.all()
        verification = verify_project_chain(project)
        return Response(
            {
                "events": EventLogSerializer(events, many=True).data,
                "verification": verification,
            }
        )

    # POST: append a client event to the hash chain.
    event_type = request.data.get("event_type")
    if event_type not in CLIENT_EVENT_TYPES:
        return Response(
            {"detail": f"Unsupported event_type '{event_type}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    payload = request.data.get("payload") or {}
    session = None
    session_id = request.data.get("session")
    if session_id:
        session = get_object_or_404(
            DraftSession, pk=session_id, project=project
        )

    # If the client reports the current content, mirror it onto the project so
    # the evidence panel and final_document_hash stay meaningful.
    if "content" in request.data:
        project.current_content = request.data["content"] or ""
        project.save(update_fields=["current_content", "updated_at"])

    event = EventLog.objects.append_event(
        project=project,
        event_type=event_type,
        payload=payload,
        session=session,
    )
    return Response(
        EventLogSerializer(event).data, status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_session(request, pk):
    project = _get_owned_project(request, pk)
    session = DraftSession.objects.create(
        project=project,
        client_info=request.data.get("client_info") or {},
    )
    EventLog.objects.append_event(
        project=project,
        event_type=EventLog.SESSION_STARTED,
        payload={"session_id": session.id},
        session=session,
    )
    return Response(
        DraftSessionSerializer(session).data, status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def end_session(request, pk):
    project = _get_owned_project(request, pk)
    session_id = request.data.get("session")
    session = get_object_or_404(DraftSession, pk=session_id, project=project)
    if session.ended_at is None:
        session.ended_at = timezone.now()
        session.save(update_fields=["ended_at"])
    EventLog.objects.append_event(
        project=project,
        event_type=EventLog.SESSION_ENDED,
        payload={"session_id": session.id},
        session=session,
    )
    return Response(DraftSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_project(request, pk):
    project = _get_owned_project(request, pk)
    if project.status not in (Project.STATUS_DRAFT, Project.STATUS_DENIED,
                              Project.STATUS_INCONCLUSIVE):
        return Response(
            {"detail": f"Cannot submit a project in status '{project.status}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project.status = Project.STATUS_SUBMITTED
    project.save(update_fields=["status", "updated_at"])
    EventLog.objects.append_event(
        project=project,
        event_type=EventLog.SUBMITTED_FOR_REVIEW,
        payload={"evidence_summary": build_evidence_summary(project)},
    )
    return Response(ProjectSerializer(project).data)


# --- Reviewer (staff only) ---------------------------------------------


@api_view(["GET"])
@permission_classes([IsReviewer])
def reviewer_projects(request):
    """List projects awaiting or having gone through review.

    Reviewers see every user's submitted/decided projects, not just their own.
    """
    qs = Project.objects.exclude(status=Project.STATUS_DRAFT)
    data = []
    for project in qs:
        row = ProjectSerializer(project).data
        row["owner_username"] = project.owner.username
        data.append(row)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsReviewer])
def reviewer_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    data = ProjectSerializer(project).data
    data["owner_username"] = project.owner.username
    data["events"] = EventLogSerializer(project.events.all(), many=True).data
    data["verification"] = verify_project_chain(project)
    data["evidence_summary"] = build_evidence_summary(project)
    data["decisions"] = ReviewDecisionSerializer(
        project.decisions.all(), many=True
    ).data
    if hasattr(project, "certificate"):
        data["certificate"] = CertificateSerializer(project.certificate).data
    return Response(data)


# Map a review decision onto the resulting project status.
_DECISION_TO_STATUS = {
    ReviewDecision.DECISION_APPROVED: Project.STATUS_APPROVED,
    ReviewDecision.DECISION_DENIED: Project.STATUS_DENIED,
    ReviewDecision.DECISION_INCONCLUSIVE: Project.STATUS_INCONCLUSIVE,
}


@api_view(["POST"])
@permission_classes([IsReviewer])
def reviewer_decision(request, pk):
    project = get_object_or_404(Project, pk=pk)
    serializer = ReviewDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    decision_value = serializer.validated_data["decision"]

    decision = serializer.save(project=project, reviewer=request.user)

    project.status = _DECISION_TO_STATUS[decision_value]
    project.save(update_fields=["status", "updated_at"])

    EventLog.objects.append_event(
        project=project,
        event_type=EventLog.REVIEW_DECISION,
        payload={
            "decision": decision_value,
            "notes": decision.notes,
            "reviewer": request.user.username,
        },
    )
    return Response(
        ReviewDecisionSerializer(decision).data, status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([IsReviewer])
def reviewer_issue_certificate(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.status != Project.STATUS_APPROVED:
        return Response(
            {"detail": "Only approved projects can be certified."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if hasattr(project, "certificate"):
        return Response(
            {"detail": "Project already has a certificate."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Sanity: refuse to certify a project whose chain does not verify.
    verification = verify_project_chain(project)
    if not verification["valid"]:
        return Response(
            {"detail": "Event chain failed verification.", "verification": verification},
            status=status.HTTP_400_BAD_REQUEST,
        )

    certificate = Certificate.objects.create(
        project=project,
        certificate_id=generate_certificate_id(),
        certification_level="Human-Origin Verified",
        final_document_hash=project.current_hash,
        evidence_summary=build_evidence_summary(project),
    )

    project.status = Project.STATUS_CERTIFIED
    project.save(update_fields=["status", "updated_at"])

    EventLog.objects.append_event(
        project=project,
        event_type=EventLog.CERTIFICATE_ISSUED,
        payload={"certificate_id": certificate.certificate_id},
    )
    return Response(
        CertificateSerializer(certificate).data, status=status.HTTP_201_CREATED
    )


# --- Public certificate -------------------------------------------------


@api_view(["GET"])
@permission_classes([AllowAny])
def public_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    return Response(CertificateSerializer(certificate).data)
