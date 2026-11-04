from django.contrib import admin
from .models import Todo

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'due_date']
    list_filter = ('status', 'priority', 'keywords')
    search_fields = ['person__first_name', 'person__last_name', 'title', 'description', 'keywords']
    date_hierarchy = 'created_at'


