"""
Tools module initialization for Smart HR Assistant.
Exports all 16 agent tools across Onboarding, Leave, Document, and Interview domains.
"""

from .onboarding_tools import (
    check_onboarding_checklist,
    start_onboarding,
    get_onboarding_progress,
    assign_buddy
)

from .leave_tools import (
    get_leave_balance,
    request_leave,
    cancel_leave_request,
    get_leave_history
)

from .document_tools import (
    find_document,
    generate_offer_letter,
    upload_document,
    get_policy_document
)

from .interview_tools import (
    schedule_interview,
    cancel_interview,
    get_interview_calendar,
    reschedule_interview
)

__all__ = [
    # Onboarding Tools (4)
    "check_onboarding_checklist",
    "start_onboarding",
    "get_onboarding_progress",
    "assign_buddy",
    # Leave Tools (4)
    "get_leave_balance",
    "request_leave",
    "cancel_leave_request",
    "get_leave_history",
    # Document Tools (4)
    "find_document",
    "generate_offer_letter",
    "upload_document",
    "get_policy_document",
    # Interview Tools (4)
    "schedule_interview",
    "cancel_interview",
    "get_interview_calendar",
    "reschedule_interview"
]
