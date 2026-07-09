from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Certificate,
    DraftSession,
    EventLog,
    Project,
    ReviewDecision,
)

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class EventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLog
        fields = [
            "id",
            "session",
            "event_type",
            "payload",
            "previous_hash",
            "event_hash",
            "created_at",
        ]
        read_only_fields = fields


class DraftSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftSession
        fields = [
            "id",
            "started_at",
            "ended_at",
            "client_info",
            "created_at",
        ]
        read_only_fields = ["id", "started_at", "created_at"]


class ProjectSerializer(serializers.ModelSerializer):
    event_count = serializers.SerializerMethodField()
    session_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "current_content",
            "current_hash",
            "status",
            "event_count",
            "session_count",
            "created_at",
            "updated_at",
        ]
        # Content and hash are NOT writable through this endpoint. All content
        # changes must flow through POST /projects/{id}/events/ so the hash
        # chain stays the single source of truth for what was written and when.
        # Only metadata like `title` is editable here.
        read_only_fields = [
            "id",
            "current_content",
            "current_hash",
            "status",
            "event_count",
            "session_count",
            "created_at",
            "updated_at",
        ]

    def get_event_count(self, obj):
        return obj.events.count()

    def get_session_count(self, obj):
        return obj.sessions.count()


class ReviewDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewDecision
        fields = ["id", "decision", "notes", "reviewer", "created_at"]
        read_only_fields = ["id", "reviewer", "created_at"]


class CertificateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "certificate_id",
            "title",
            "certification_level",
            "final_document_hash",
            "evidence_summary",
            "status",
            "issued_at",
            "revoked_at",
        ]
        read_only_fields = fields
