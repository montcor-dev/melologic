from django.db import models
from django.utils import timezone


class InteractionType(models.TextChoices):
    # Interaction type choices for Interaction model.

    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    SMS = 'sms', 'SMS'    
    MESSENGER = 'messenger', 'Messenger'
    VIDEOCALL = 'video_call', 'Video Call'
    INPERSON = 'inperson', 'In Person'
    MAIL = 'mail', 'Mail'
    OTHER = 'other', 'Other'
    INTERNAL_NOTE = 'internal_note', 'Internal Note'


class Interaction(models.Model):
    # Track communication/interaction history with persons.

    interaction_date = models.DateTimeField(default=timezone.now)
    person = models.ForeignKey('persons.Person', on_delete=models.PROTECT, related_name='interactions')
    author = models.ForeignKey('persons.Person',on_delete=models.PROTECT, related_name='interactions_author')
    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        blank=False, 
        null=False
    )
    subject = models.CharField(max_length=200)
    note = models.TextField(blank=False)
    keywords = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="Keywords for filtering (e.g. invoicing, urgent, scheduling)"
    )
    follow_up_needed = models.BooleanField(default=False)
    follow_up_due_date = models.DateField(blank=True, null=True)


    class Meta:
        ordering = ['-interaction_date']
        verbose_name = 'Interaction'
        verbose_name_plural = 'Interactions'

    def __str__(self):
        # Return human-readable representation of the interaction.
        return f"{self.get_interaction_type_display()} with {self.person} on {self.interaction_date.strftime('%Y-%m-%d')}"