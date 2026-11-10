from django.contrib import admin, messages

from .models import Term, Room, Enrollment, Lesson, LessonParticipant
from .services import approve_enrollment

@admin.register(Enrollment)
class EnrollmentAdmin (admin.ModelAdmin):
    list_display = ["student", "teacher", "term", "frequency", "lessons_agreed", "status"]
    list_filter = ["status", "term", "teacher"]
    actions = ["approve_selected"]

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
