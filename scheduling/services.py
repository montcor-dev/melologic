from django.db import transaction
from django.utils import timezone

from .models import Enrollment, Lesson, LedgerEntry


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


    # add the ledger grant for the chosen enrollment
    ledger_grant = enrollment.lesson_duration * enrollment.lessons_agreed
    LedgerEntry.objects.create(
            enrollment=enrollment,
            minutes=ledger_grant,
            reason=LedgerEntry.Reason.PURCHASE,
    )

    return enrollment