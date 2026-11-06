from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Todo

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'person', 'status', 'priority', 'due_date', 'interaction_link')
    list_filter = ('status', 'priority')
    search_fields = ('person__first_name', 'person__last_name', 'title', 'description', 'keywords', 'interaction__subject')
    date_hierarchy = 'created_at'

    autocomplete_fields = ('person',)


    def interaction_link(self, obj):
        """
        Return a clickable link to view a related interaction for this todo.
        
        This method is called by Django admin for each row in the list view.
        The 'obj' parameter is the todo instance for that row.
        
        Example output: <a href="/admin/interactions/interaction/14/change/">View</a>
        
        Args:
            obj: The todo instance for this row
            
        Returns:
            Safe HTML string containing the link
        """

        if obj.interaction:  # If the todo has a related interaction

            # Step 1: Build the base admin URL for viewing an Interaction
            # reverse() looks up the URL by name (more robust than hardcoding)
            url = reverse('admin:interactions_interaction_change', args=[obj.interaction.id])
            
            # Step 2: Build the HTML link safely
            # format_html() escapes variables automatically (security against XSS attacks)
            return format_html(
                '<a href="{}">View</a>',
                url
            )
        else:
            return ""
    
    # Tell Django this method returns safe HTML (don't escape the link)
    interaction_link.short_description = 'Interactions'  # Column header text