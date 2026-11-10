from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from persons.models import Person, Student, Teacher
from scheduling.models import Enrollment, Lesson, LessonParticipant, Room, Term
from scheduling.services import approve_enrollment


class ApproveEnrollmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Runs once for the whole class. Creates the shared objects.
        cls.student = Student.objects.create(
            person=Person.objects.create(first_name="Anna", last_name="Meier")
        )
        cls.teacher = Teacher.objects.create(
            person=Person.objects.create(first_name="Paul", last_name="Berger")
        )
        cls.term = Term.objects.create(
            name="S26|02", start_date=date(2026, 8, 24), end_date=date(2027, 1, 30)
        )
        cls.room = Room.objects.create(name="Salle 1")
        cls.user = get_user_model().objects.create_user("admin", password="x")

    def make_enrollment_with_lessons(self, count=2):
        enrollment = Enrollment.objects.create(
            student=self.student, teacher=self.teacher, term=self.term, frequency=Enrollment.Frequency.WEEKLY,
            lesson_duration=45, lessons_agreed=count,
            status=Enrollment.Status.PROPOSED,
        )
        start = timezone.now() + timedelta(days=7)
        for i in range(count):
            lesson = Lesson.objects.create(
                teacher=self.teacher, room=self.room,
                start=start + timedelta(weeks=i),
                end=start + timedelta(weeks=i, minutes=45),
                status=Lesson.Status.PROVISIONAL,
            )
            LessonParticipant.objects.create(
                lesson=lesson, student=self.student, enrollment=enrollment
            )
        return enrollment

    def test_approval_activates_enrollment_and_confirms_lessons(self):
        enrollment = self.make_enrollment_with_lessons(count=2)

        approve_enrollment(enrollment, actor=self.user)

        enrollment.refresh_from_db()  # reload from the database
        self.assertEqual(enrollment.status, enrollment.Status.ACTIVE)
        self.assertIsNotNone(enrollment.approved_at)
        self.assertEqual(
            Lesson.objects.filter(status=Lesson.Status.SCHEDULED).count(), 2
        )
        self.assertFalse(Lesson.objects.filter(status=Lesson.Status.PROVISIONAL).exists()
        )

    def test_approval_does_not_touch_cancelled_lessons(self):
        enrollment = self.make_enrollment_with_lessons(count=1)
        Lesson.objects.update(status=Lesson.Status.CANCELLED)

        approve_enrollment(enrollment, actor=self.user)

        self.assertEqual(Lesson.objects.get().status, Lesson.Status.CANCELLED)
