from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from persons.models import Person, Student, Teacher
from scheduling.models import Enrollment, Lesson, LessonParticipant, Room, Term, LedgerEntry
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


    # Helper method that creates an Enrollment instance for the tests
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


    # Test methods
    def test_approval_activates_enrollment_and_confirms_lessons(self):
        enrollment = self.make_enrollment_with_lessons(count=2)  # arrange
        approve_enrollment(enrollment, actor=self.user)  # act
        enrollment.refresh_from_db()  # reload (from the database)
        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)  # assert
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

    def test_enrollment_without_lessons_activates(self):
        enrollment = self.make_enrollment_with_lessons(count=0)  # arrange
        approve_enrollment(enrollment, actor=self.user)  # act
        enrollment.refresh_from_db()  # reload from db
        self.assertEqual(enrollment.status, enrollment.Status.ACTIVE)  #assert

    def test_approval_adds_correct_minutes_to_ledger(self):
        enrollment = self.make_enrollment_with_lessons(count=9)  # arrange
        expected = enrollment.lessons_agreed * enrollment.lesson_duration
        approve_enrollment(enrollment, actor=self.user)  # act
        self.assertEqual(enrollment.balance_min(), expected)  # assert

    def test_approving_twice_the_same_enrollment_is_refused(self):        
        enrollment = self.make_enrollment_with_lessons(count=2)  # arrange
        approve_enrollment(enrollment, actor=self.user)  # act (1st approval works)

        with self.assertRaises(ValidationError):  
            approve_enrollment(enrollment, actor=self.user)  # 2nd is refused

        self.assertEqual(enrollment.balance_min(), 90)  # assert



class LedgerEntryTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.student = Student.objects.create(
            person=Person.objects.create(first_name="Alain", last_name="Delon") 
        )
        cls.teacher = Teacher.objects.create(
            person=Person.objects.create(first_name="Patty", last_name="Smith")
        )
        cls.term = Term.objects.create(name="S26|01", start_date=date(2026, 9, 1), end_date=date(2027, 1, 30)
        )
        cls.enrollment = Enrollment.objects.create(student=cls.student, teacher=cls.teacher, term=cls.term, frequency=Enrollment.Frequency.WEEKLY, lesson_duration=Enrollment.Duration.MIN_45, lessons_agreed=9)


    # Test methods
    def test_cancel_reason_with_empty_note_is_allowed(self):
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=-45,
            reason=LedgerEntry.Reason.CANCEL,
            note="",
        )
        self.assertEqual(LedgerEntry.objects.count(), 1) 
    
    def test_manual_reason_with_note_is_allowed(self):
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=45,
            reason=LedgerEntry.Reason.MANUAL,
            note="Correction for vacation week.",
        )
        self.assertEqual(LedgerEntry.objects.count(), 1) 

    def test_manual_reason_with_empty_note_raises_error(self):        
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LedgerEntry.objects.create(
                    enrollment=self.enrollment,
                    minutes=45,
                    reason=LedgerEntry.Reason.MANUAL,
                    note="",
                )




class BalanceMinTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.student = Student.objects.create(
            person=Person.objects.create(first_name="Alain", last_name="Delon") 
        )
        cls.teacher = Teacher.objects.create(
            person=Person.objects.create(first_name="Patty", last_name="Smith")
        )
        cls.term = Term.objects.create(name="S26|01", start_date=date(2026, 9, 1), end_date=date(2027, 1, 30)
        )
        cls.enrollment = Enrollment.objects.create(student=cls.student, teacher=cls.teacher, term=cls.term, frequency=Enrollment.Frequency.WEEKLY, lesson_duration=Enrollment.Duration.MIN_45, lessons_agreed=9)


    # Test methods
    def test_balance_of_new_enrollment_is_zero(self):
        self.assertEqual(self.enrollment.balance_min(), 0)
    
    def test_total_of_several_entries_is_correct(self):
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=810,
            reason=LedgerEntry.Reason.PURCHASE,
            note="",
        )
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=-225,
            reason=LedgerEntry.Reason.LESSON_USED,
            note="",
        )
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=-45,
            reason=LedgerEntry.Reason.CANCEL,
            note="",
        )
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=45,
            reason=LedgerEntry.Reason.MAKEUP,
            note="",
        )
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=-45,
            reason=LedgerEntry.Reason.CANCEL,
            note="",
        )

        self.assertEqual(self.enrollment.balance_min(), 540)

    def test_other_enrollments_dont_count(self):
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=810,
            reason=LedgerEntry.Reason.PURCHASE,
            note="",
        )
        LedgerEntry.objects.create(
            enrollment=self.enrollment,
            minutes=-45,
            reason=LedgerEntry.Reason.CANCEL,
            note="",
        )

        new_enrollment = Enrollment.objects.create(student=self.student, teacher=self.teacher, term=self.term, frequency=Enrollment.Frequency.WEEKLY, lesson_duration=Enrollment.Duration.MIN_45, lessons_agreed=9)

        LedgerEntry.objects.create(
            enrollment=new_enrollment,
            minutes=45,
            reason=LedgerEntry.Reason.MANUAL,
            note="trial lesson",
        )

        self.assertEqual(self.enrollment.balance_min(), 765)
        self.assertEqual(new_enrollment.balance_min(), 45)