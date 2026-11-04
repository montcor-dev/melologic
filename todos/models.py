from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class TodoStatus(models.TextChoices):
    """Status choices for Todo model."""
    NEW = 'new', 'New'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Todo(models.Model):
    """
    Track action items and tasks for the music school.
    
    Todos can be linked to a specific person (e.g., student follow-up)
    or be general tasks (e.g., 'Order sheet music'). When an Interaction
    has follow_up_needed=True, a Todo is automatically created.
    
    Keywords are stored as a PostgreSQL ArrayField for efficient querying
    and filtering (e.g., show all 'urgent' or 'invoicing' tasks).
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Optional details about this task")
    status = models.CharField(
        max_length=20,
        choices=TodoStatus.choices,
        default=TodoStatus.NEW,
        help_text="Current status of this todo"
    )
    priority = models.IntegerField(
        choices=[(1, 'Low'), (2, 'Normal'), (3, 'High'), (4, 'Urgent')],
        default=2,
        help_text="Task priority (1=Low, 4=Urgent)"
    )
    person = models.ForeignKey(
        'persons.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='todos',
        help_text="Optional: link this todo to a specific person"
    )
    keywords = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="Keywords for filtering (e.g. invoicing, urgent, scheduling)"
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']  # Newest first
        verbose_name = 'Todo'
        verbose_name_plural = 'Todos'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Automatically set completed_at when status changes to COMPLETED.
        Automatically clear completed_at when status changes away from COMPLETED.
        """
        if self.status == TodoStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != TodoStatus.COMPLETED and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)
