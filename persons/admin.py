from django.contrib import admin
from .models import Person, Student, Teacher

class StudentInline(admin.StackedInline):
    model = Student
    extra = 0
    max_num = 1

class TeacherInline(admin.StackedInline):
    model = Teacher
    extra = 0
    max_num = 1

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'birth_date']
    
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


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'status', 'level', 'instruments']

    def get_name(self, obj):
        """Return student's full name from related Person"""
        return f"{obj.person.last_name} {obj.person.first_name}"

    # Makes column sortable by last name
    get_name.admin_order_field = 'person__last_name'

    # Changes the column header to 'Name'
    get_name.short_description = 'Name'


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