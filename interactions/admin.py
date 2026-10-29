from django.contrib import admin
from .models import Interaction

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['interaction_date', 'person', 'author', 'note', 'interaction_type', 'follow_up_needed']
    search_fields = ['person__first_name', 'person__last_name', 'note', 'author__first_name', 'author__last_name']
    date_hierarchy = 'interaction_date'
