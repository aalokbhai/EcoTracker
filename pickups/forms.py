from django import forms
from django.utils import timezone

from accounts.i18n import tr

from .models import PickupRequest


class PickupForm(forms.ModelForm):
    class Meta:
        model = PickupRequest
        fields = ['waste_type', 'address', 'preferred_date', 'notes']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'waste_type': 'Waste type', 'address': 'Address',
                  'preferred_date': 'Preferred date', 'notes': 'Notes'}
        placeholders = {'address': 'Full pickup address',
                        'notes': 'Anything the collector should know (optional)'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])
            if name in placeholders:
                field.widget.attrs['placeholder'] = tr(placeholders[name])
        wt = self.fields['waste_type']
        wt.widget.attrs['class'] = 'form-select'
        wt.choices = [('', tr('Select waste type'))] + [
            (value, tr(label)) for value, label in PickupRequest.WASTE_TYPE_CHOICES]

    def clean_preferred_date(self):
        date = self.cleaned_data['preferred_date']
        if date < timezone.localdate():
            raise forms.ValidationError(tr('Please choose today or a future date.'))
        return date