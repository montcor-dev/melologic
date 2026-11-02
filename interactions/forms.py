from django import forms
from .models import Interaction	 

class InteractionForm(forms.ModelForm): 

    def clean(self):
        cleaned_data = super().clean()
        follow_up_needed = cleaned_data.get('follow_up_needed')
        follow_up_due_date = cleaned_data.get('follow_up_due_date')
        if not follow_up_needed and follow_up_due_date is not None:
            # Attach error to the follow_up_due_date field
            self.add_error('follow_up_due_date', 'A due date is only allowed when follow-up is needed.')	
        return cleaned_data