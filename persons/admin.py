from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Person, Student, Teacher

admin.site.site_header = 'Melologic - musique school app'
admin.site.site_title = 'Melologic - admin'
admin.site.index_title = ''

class StudentInline(admin.StackedInline):
    model = Student
    extra = 0
    max_num = 1

class TeacherInline(admin.StackedInline):
    model = Teacher
    extra = 0
    max_num = 1

class RoleFilter(admin.SimpleListFilter):
    # custom filter to categorize persons by their role

    # --- Class attributes ---

    title  = 'Role'
    # title shown above the filter in the admin sidebar

    parameter_name = 'role'
    # url parameter name when filer is active


    # --- Define filter choices ---

    def lookups(self, request, model_admin):
        """
        returns the choices shown in the dropdown

        Args:
            - request: current http request
            - model_admin: the admin class (PersonAdmin)

        Returns:
            List of tuples (internal_value, display_text)
                - internal_value: what goes in the url (?role=student)
                - display_text: text visible in dropdown        
        """

        return (
            ('student', 'Student'),
            ('teacher', 'Teacher'),
            ('both', 'Both (Student & Teacher)'),
            ('none', 'No role (general contact)'),
        )

    # --- Filter the database query ---

    def queryset(self, request, queryset):
        """
        filters the database query based on selected choice

        Django calls this method when a user clicks a filter option.

        Args:
            - request: current http request
            - queryset: the current databse query (all Person records)

        Returns:
            A filtered queryset (subset of persos)
        """

        # self.value() returns the selected internal_value from lookups()
        # Example: 'student', 'teacher', 'both', or 'none'

        if self.value() == 'student':
            return queryset.filter(
                student__isnull=False
            )

        elif self.value() == 'teacher':
            return queryset.filter(
                teacher__isnull=False
            )

        elif self.value() == 'both':
            return queryset.filter(
                student__isnull=False,
                teacher__isnull=False
            )

        elif self.value() == 'none':
            return queryset.filter(
                student__isnull=True,
                teacher__isnull=True
            )

        # if no filter selected, return original queryset
        return queryset


class TeacherFilter(admin.SimpleListFilter):
    # custom filter to show only the students of a selected teacher

    # --- Class attributes ---
    title = 'Teacher'
    parameter_name = 'teacher'

    # --- Define filter choices ---

    def lookups(self, request, model_admin):
        teachers = Teacher.objects.all()
        return [(t.id, f"{t.person.last_name} {t.person.first_name}") for t in teachers]

    # -- Filter the database query ---

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(teacher_id=self.value())
        return queryset


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'role', 'email', 'phone', 'add_interaction_link']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = [RoleFilter, 'city']
    
    fieldsets = (
        ('Identity', {
            'fields': ('title', 'first_name', 'last_name', 'birth_date')
        }),
        ('Contact', {
            'fields': ('address', 'postal_code', 'city', 'phone', 'phone_2', 'email')
        }),
        ('Preferences', {
            'fields': ('greeting_formula', 'use_tu', 'about_me')
        }),
    )
    
    inlines = [StudentInline, TeacherInline]

    def full_name(self, obj):
        """
        Return formatted full name for list display.
        
        This method is used in list_display to show the person's name
        as 'lastname firstname' instead of separate columns.
        
        Args:
            obj: The Person instance being displayed
            
        Returns:
            str: Formatted name string
        """
        return f"{obj.last_name} {obj.first_name}"
    
    # Makes the column sortable by last_name
    full_name.admin_order_field = 'last_name'
    
    # Sets the column header text
    full_name.short_description = 'Name'


    def role(self, obj):
        """
        Method to display a person's role (ex. student, teacher) in a column

        obj is the Person instance
        """

        roles = []
        if obj.student_set.exists():
            roles.append('Student')
        if obj.teacher_set.exists():
            roles.append('Teacher')
        return ', '.join(roles) if roles else '---'


    def add_interaction_link(self, obj):
        """
        Return a clickable link to create a new interaction for this person.
        
        This method is called by Django admin for each row in the list view.
        The 'obj' parameter is the Person instance for that row.
        
        Example output: <a href="/admin/interactions/interaction/add/?person=12">Add Interaction</a>
        
        Args:
            obj: The Person instance for this row
            
        Returns:
            Safe HTML string containing the link
        """
        # Step 1: Build the base admin URL for adding an Interaction
        # reverse() looks up the URL by name (more robust than hardcoding)
        url = reverse('admin:interactions_interaction_add')
        
        # Step 2: Add the person ID as a query parameter
        # This pre-fills the 'person' field in the new interaction form
        full_url = f"{url}?person={obj.id}"
        
        # Step 3: Build the HTML link safely
        # format_html() escapes variables automatically (security against XSS attacks)
        return format_html(
            '<a href="{}" class="button">Add Interaction</a>',
            full_url
        )
    
    # Tell Django this method returns safe HTML (don't escape the link)
    add_interaction_link.short_description = 'Actions'  # Column header text


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'teacher', 'status', 'level', 'instruments']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = [TeacherFilter, 'status']

    def get_name(self, obj):
        """Return student's full name from related Person"""
        return f"{obj.person.last_name} {obj.person.first_name}"

    # Makes column sortable by last name
    get_name.admin_order_field = 'person__last_name'

    # Changes the column header to 'Name'
    get_name.short_description = 'Name'


    # Makes 'person' field readonly when in 'change' view
    # This hides the dropdown and adds a link at the bottom to the person's change view
    def get_readonly_fields(self, request, obj=None):
        return ['person'] if obj else []

    # Hide ADD STUDENT+ button in persons/student view
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'status', 'instruments']

    def get_name(self, obj):
        """Return student's full name from related Person"""
        return f"{obj.person.last_name} {obj.person.first_name}"

    # Makes column sortable by last name
    get_name.admin_order_field = 'person__last_name'

    # Changes the column header to 'Name'
    get_name.short_description = 'Name'

    # Makes 'person' field readonly when in 'change' view
    # This hides the dropdown and adds a link at the bottom to the person's change view
    def get_readonly_fields(self, request, obj=None):
        return ['person'] if obj else []

    # Hide ADD TEACHER+ button in persons/teacher view
    def has_add_permission(self, request, obj=None):
        return False