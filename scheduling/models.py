from django.core.exceptions import ValidationError
from django.db import models



class Term(models.Model):
    """ A semester. Only a scheduling anchor; the lesson count lives in Enrollment. """
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["start_date"]  # newest term first everywhere

    def __str__(self):
        return self.name

    def clean(self):
        # clea() is a Django hook method for validation across several fields.
        # It runs in the admin and in ModelForms, but NOT on plain .save()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("The end date cannot be befor the start date.")



class Room(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_online = models.BooleanField(default=False)  # video conferencing "room"

    def __str__(self):
        return self.name



class Enrollment(models.Model):

    class Frequency(models.TextChoices):
        # TextChoices: value stored in DB, label shown to users
        WEEKLY = "weekly", "Every week"
        BIWEEKLY = "biweekliy", "Every other week"
    
    class Duration(models.IntegerChoices):
        MIN_30 = 30, "30 minutes"
        MIN_45 = 45, "45 minutes"
        MIN_60 = 60, "60 minutes"
        MIN_90 = 90, "90 minutes"

    class Status(models.TextChoices):
    DRAFT = "draft", "Draft (being planned)"
    PROPOSED = "proposed", "Proposed (sent to student)"
    ACTIVE = "active", "Active (approved)"
    ENDED = "ended", "Ended"


    # on_delete=models.PROTECT: impossible to delete a student who still has enrollments (safer than CASCADE).
    student = models.ForeignKey(
        "persons.Student", on_delete=models.PROTECT, related_name="enrollments"
    )
    teacher = models.ForeignKey(
        "persons.Teacher", on_delete=models.PROTECT,
        related_name="enrollments"
    )
    term = models.ForeignKey(
        Term, on_delete=models.PROTECT, related_name="enrollments"
    )
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    lesson_duration = models.PositiveSmallIntegerField(choices=Duration.choices)
    lessons_agreed = models.PositiveSmallIntegerField(
        help_text="Agreed number of lessons (9 or 18 for a full term, less if prorated)."
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    proposed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-term__start_date", "student__id"]

    def __str__(self):
        return f"{self.student} / {self.teacher} / {self.term}"



class Lesson(models.Model):
    """ One calendar event. Who attends (and under which enrollment) is in LessonParticipant. """
    
    class Status(models.TextChoices):
        PROVISIONAL = "provisional", "Provisional (awaiting approval)"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    teacher = models.ForeignKey(
        "persons.Teacher", on delete=models.PROTECT,
        related_name="lessons"
    )
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="lessons")
    start = models.DateField()
    end = models.DateField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PROVISIONAL
    )

    class Meta:
        ordering = ["start"]
        indexes = [models.Index(fields=["start"])]  # The calendar feed filters by date range
        constraints = [
            # Data integrity is the one thing we enforce at DB level.
            models.CheckConstraint(
                condition=models.Q(end_gt=models.F("start")),
                name="lesson_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.start:%Y-%m-%d %H:%M} ({self.teacher})"

    @property
    def is_group(self):
        # Derived, not stored: a lesson is a group lesson if it has 2+ participants.
        return self.participants.count() >= 2



class LessonParticipant(models.Model):

    class Attendance(models.TextChoices):
        EXPECTED = "expected", "Expected"
        PRESENT = "present", "Present"
        ABSENT_STUDENT = "absent_student", "Absent (students)"
        ABSENT_TEACHER = "absent_teacher", "Absent (teacher)"
        NO_SHOW = "no_show", "No-show"

    lesson = models.ForeignKey(
        Lesson, on_delete=CASCADE, related_name="participants"
    )
    student = models.ForeignKey(
        "persons.Student", on_delete=models.PROTECT, related_name="lesson_participants"
    )
    enrollment = models.ForeignKey(
        Enrollment, on_delete=PROTECT, related_name="participants"
    )
    attendance_status = models.CharField(
        max_length=20, choices=Attendance.choices, default=Attendance.EXPECTED
    )

    class Meta:
        constraints = [
            # The same student cannot be added twice to one lesson.
            models.UniqueConstraint(
                fields=["lesson", "student"], name="unique_student_per_lesson"
            ),
        ]

    def __str__(self):
        return f"{self.student} @ {self.lesson}"

    def clean(self)
        # The participant's student must be the student of the enrollment.
        if self.enrollment_id and self.student_id:
            if self.enrollment.student_id != self.student_id:
                raise ValidationError("The enrollment belongs to a different student.")