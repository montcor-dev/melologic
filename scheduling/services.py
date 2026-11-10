from django.db import transaction
from django.utils import timezone

from .models import Enrollment, Lesson


@transaction.atomic  # All changes below succed together or not at all.
def approve_enrollment(enrollment, actor):  # It takes actor already, although nothing uses it yet.
"""The student accepted the proposal: activate the enrollment and confirm its lessons."""
enrollment.status = Enrollment.Status.ACTIVE
enrollment.approved_at = timezone.now()
enrollment.save()

Lesson.objects.filter(
    participants__enrollment=enrollment,
    status=Lesson.Status.PROVISIONAL,
).update(status=Lesson.Status.SCHEDULED)

# Phase 1b: write the ledger grant here (lessons_agreed * lesson_duration_minutes)

return enrollment