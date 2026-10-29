from django.contrib import admin
from .models import Interaction

# Person ID for the default author
DEFAULT_AUTHOR_ID = 295



@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['interaction_date', 'person', 'author', 'note', 'interaction_type', 'follow_up_needed']
    list_filter = ('interaction_type', 'follow_up_needed', 'interaction_date')
    search_fields = ['person__first_name', 'person__last_name', 'note', 'author__first_name', 'author__last_name']
    date_hierarchy = 'interaction_date'

    def get_changeform_initial_data(self, request):
        """
        Set default values for new Interaction forms.
        
        This method is only called when creating a new object (not editing).
        It allows us to pre-fill fields based on URL parameters or defaults.
        
        Example URL: /admin/interactions/interaction/add/?person=5
        - If 'author' is in the URL, use that value
        - Otherwise, default to the main user (DEFAULT_AUTHOR_ID)
        """

        """Pre-fill author and person fields when creating new interactions."""
        return {
            'author': request.GET.get('author', DEFAULT_AUTHOR_ID),
            'person': request.GET.get('person', None),  # Optional: pre-fill person too
        }