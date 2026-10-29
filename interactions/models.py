from django.db import models
from django.utils import timezone

class InteractionType(models.TextChoices):
    # Interaction type choices for Interaction model.
    
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    SMS = 'sms', 'Sms'
    VIDEOCALL = 'video_call', 'Video Call'
    MESSENGER = 'messenger', 'Messenger'
    INPERSON = 'inperson', 'In Person'
    MAIL = 'mail', 'Mail'
    OTHER = 'other', 'Other'

class Interaction(models.Model):
    interaction_date = models.DateField(blank=False, null=True)
    person = models.ForeignKey('persons.Person', on_delete=models.PROTECT, related_name='interactions')
    author = models.ForeignKey('persons.Person',on_delete=models.PROTECT)
    note = models.TextField(blank=True)
    follow_up_needed = models.BooleanField(default=False)
    follow_up_due_date = models.DateField(blank=True, null=True)
    interaction_type = models.models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        blank=True, 
        null=True
    )

    class Meta:
        ordering = ['-interaction_date']
        verbose_name = 'Interaction'
        verbose_name_plural = 'Interactions'

    def __str__(self):
        """ Return interaction type for admin. """
        return f"{self.get_interaction_type_display()} with {self.person} on {self.interaction_date.strftime('%Y-%m-%d')}"