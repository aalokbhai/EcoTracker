import re

from django import forms
from django.utils import timezone

from accounts.i18n import tr

from .models import PickupRequest


class PickupForm(forms.ModelForm):
    class Meta:
        model = PickupRequest
        fields = ['waste_type', 'preferred_date', 'address', 'area', 'city', 'state', 'pincode', 'notes']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'waste_type': 'Waste type', 'preferred_date': 'Preferred date',
                  'address': 'House no. / Street / Landmark', 'area': 'Area',
                  'city': 'City', 'state': 'State', 'pincode': 'Pincode', 'notes': 'Notes'}
        placeholders = {'address': 'House no., street or nearby landmark',
                        'area': 'e.g. Civil Lines', 'city': 'e.g. Kanpur',
                        'state': 'e.g. Uttar Pradesh', 'pincode': '6-digit pincode',
                        'notes': 'Anything the collector should know (optional)'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])
            if name in placeholders:
                field.widget.attrs['placeholder'] = tr(placeholders[name])
        for name in ('area', 'city', 'state', 'pincode'):
            self.fields[name].required = True
        self.fields['pincode'].widget.attrs['inputmode'] = 'numeric'
        wt = self.fields['waste_type']
        wt.widget.attrs['class'] = 'form-select'
        wt.choices = [('', tr('Select waste type'))] + [
            (value, tr(label)) for value, label in PickupRequest.WASTE_TYPE_CHOICES]

    def clean_preferred_date(self):
        date = self.cleaned_data['preferred_date']
        if date < timezone.localdate():
            raise forms.ValidationError(tr('Please choose today or a future date.'))
        return date

    def clean_area(self):
        return self.cleaned_data['area'].strip().title()

    def clean_city(self):
        return self.cleaned_data['city'].strip().title()

    def clean_state(self):
        return self.cleaned_data['state'].strip().title()

    def clean_pincode(self):
        value = self.cleaned_data['pincode'].strip()
        if not re.fullmatch(r'\d{6}', value):
            raise forms.ValidationError(tr('Enter a valid 6-digit pincode.'))
        return value
