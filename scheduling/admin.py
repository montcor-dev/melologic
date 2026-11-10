from django.contrib import admin, messages

from .models import Term, Room, Enrollment, Lesson, LessonParticipant
from .services import approve_enrollment

@admin.register(Enrollment)
class EnrollmentAdmin (admin.ModelAdmin):
    list_display = ["student_name", "teacher", "term", "frequency", "lessons_agreed", "status"]
    list_filter = ["status", "term", "teacher"]
    list_selected_related = ["student__person", "teacher__pernson", "term"]
    actions = ["approve_selected"]

    @admin.display(description="Student", ordering="student__person__last_name")
    def student_name(self, obj):
        return f"{obj.student.person.last_name} {obj.student.person.first_name}"
    
    @admin.action(description="Approve selected enrollments (student accepted)")
    def approve_selected(self, request, queryset):
        for enrollment in queryset:
            approve_enrollment(enrollment, actor=request.user)
        self.message_user(request, f"{queryset.count()} enrollment(s) approved.", messages.SUCCESS)

class LessonParticipantInline(admin.TabularInline):
    # Let's edit participants on the Lesson page itself.
    model = LessonParticipant
    extra = 1


@admin.register(Lesson)
class LessonAdmin (admin.ModelAdmin):
    list_display = ["start", "end", "teacher", "room", "status"]
    list_filter = ["status", "teacher", "room"]
    date_hierarchy = "start"
    inlines = [LessonParticipantInline]


@admin.register(Term)
class TermAdmin (admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    list_filter = ["name"]
    date_hierarchy = "start_date"


@admin.register(Room)
class RoomAdmin (admin.ModelAdmin):
    list_display = ["name", "is_online"]
    list_filer = ["name"]
