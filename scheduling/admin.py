from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Term, Room, Enrollment, Lesson, LessonParticipant, LedgerEntry
from .services import approve_enrollment

@admin.register(Enrollment)
class EnrollmentAdmin (admin.ModelAdmin):
    list_display = ["student_name", "teacher", "term", "frequency", "lessons_agreed", "status"]
    list_filter = ["status", "term", "teacher"]
    list_selected_related = ["student__person", "teacher__person", "term"]
    actions = ["approve_selected"]

    @admin.display(description="Student", ordering="student__person__last_name")
    def student_name(self, obj):
        return f"{obj.student.person.last_name} {obj.student.person.first_name}"
    
    @admin.action(description="Approve selected enrollments (student accepted)")
    def approve_selected(self, request, queryset):
        approved = 0
        for enrollment in queryset:
            try:
                approve_enrollment(enrollment, actor=request.user)
                approved += 1
            except ValidationError as e:
                self.message_user(request, " ".join(e.messages), messages.ERROR)
        if approved:
            self.message_user(request, f"{approved} enrollment(s) approved.", messages.SUCCESS)

class LessonParticipantInline(admin.StackedInline):
    # Let's edit participants on the Lesson page itself.
    model = LessonParticipant
    extra = 1


@admin.register(Lesson)
class LessonAdmin (admin.ModelAdmin):
    list_display = ["start", "end", "students", "teacher", "room", "status"]
    list_filter = ["status", "teacher", "room", "participants__student__person__last_name"]
    search_fields = ["participants__student__person__last_name", "participants__student__person__first_name"]
    date_hierarchy = "start"
    inlines = [LessonParticipantInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("participants__student__person", "teacher__person")

    @admin.display(description="Student(s)")
    def students(self, obj):
        return ", ".join(
            f"{p.student.person.last_name} {p.student.person.first_name}"
            for p in obj.participants.all()
        )


@admin.register(Term)
class TermAdmin (admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    list_filter = ["name"]
    date_hierarchy = "start_date"


@admin.register(Room)
class RoomAdmin (admin.ModelAdmin):
    list_display = ["name", "is_online"]
    list_filer = ["name"]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "minutes", "reason", "created_at")
    list_filter = ("reason", "enrollment__term")
    list_select_related = ("enrollment__student__person", "enrollment__teacher__person", "enrollment__term")
    readonly_fields = ("created_at",)
    search_fields = ('enrollment__student__person__first_name', 'enrollment__student__person__last_name', 'note')