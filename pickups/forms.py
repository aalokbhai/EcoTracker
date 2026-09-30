from django import forms
from django.utils import timezone
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
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['waste_type'].widget.attrs['class'] = 'form-select'

    def clean_preferred_date(self):
        date = self.cleaned_data['preferred_date']
        if date < timezone.localdate():
            raise forms.ValidationError('Purani date select nahi kar sakte.')
        return date