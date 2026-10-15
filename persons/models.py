from django.db import models


class Person(models.Model):
    title = models.CharField(max_length=20, blank=True, null=True)
    greeting_formula = models.CharField(max_length=20, blank=True, null=True)
    use_tu = models.BooleanField(blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    address = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    phone_2 = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    about_me = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set once, on create
    updated_at = models.DateTimeField(auto_now=True)       # Updated on every save

    def __str__(self):
        """ Return name for admin and dropdowns (instead of ID). """
        return f"{self.last_name} {self.first_name}"


class StudentStatus(models.TextChoices):
    """
    Status choices for Student model.
    
    These values represent the student lifecycle from initial contact
    (prospect) through active enrollment (active) to former student (former).
    The 'lost' status tracks prospects/students who discontinued.
    """
    PROSPECT = 'prospect', 'Prospect'
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    FORMER = 'former', 'Former'
    LOST = 'lost', 'Lost'
    

class Student(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StudentStatus.choices,
        blank=True, 
        null=True
    )
    level = models.CharField(max_length=20, blank=True, null=True)
    styles = models.CharField(max_length=30, blank=True, null=True)
    instruments = models.CharField(max_length=50, blank=True, null=True)
    source = models.CharField(max_length=20, blank=True, null=True)
    first_contact_date = models.DateField(blank=True, null=True)
    enrollment_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set once, on create
    updated_at = models.DateTimeField(auto_now=True)       # Updated on every save

    def __str__(self):
        """ Return student name with status for admin. """
        return f"{self.person.last_name} {self.person.first_name} - {self.status}"


class Teacher(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    styles = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    instruments = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set once, on create
    updated_at = models.DateTimeField(auto_now=True)       # Updated on every save

    def __str__(self):
        """ Return teacher name with status for admin. """
        return f"{self.person.last_name} {self.person.first_name}"
