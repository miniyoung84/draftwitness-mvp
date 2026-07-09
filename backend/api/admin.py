from django.contrib import admin

from .models import (
    Certificate,
    DraftSession,
    EventLog,
    Project,
    ReviewDecision,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "owner__username")


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "event_type", "event_hash", "created_at")
    list_filter = ("event_type",)
    # Hashes are read-only in the admin; editing them here would defeat the
    # tamper-evidence guarantee.
    readonly_fields = ("previous_hash", "event_hash", "created_at_iso")


@admin.register(DraftSession)
class DraftSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "started_at", "ended_at")


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "decision", "reviewer", "created_at")
    list_filter = ("decision",)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "project", "status", "issued_at")
    list_filter = ("status", "certification_level")
    search_fields = ("certificate_id",)
