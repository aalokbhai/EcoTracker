import re

from django import forms

from accounts.i18n import tr

from .models import Complaint


def _validate_pincode(value):
    value = value.strip()
    if not re.fullmatch(r'\d{6}', value):
        raise forms.ValidationError(tr('Enter a valid 6-digit pincode.'))
    return value


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'area', 'address', 'city', 'state', 'pincode', 'description', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'category': 'Category', 'area': 'Area', 'address': 'Street / Landmark',
                  'city': 'City', 'state': 'State', 'pincode': 'Pincode',
                  'description': 'Description', 'image': 'Photo'}
        placeholders = {'area': 'e.g. Civil Lines',
                        'address': 'House no., street or nearby landmark',
                        'city': 'e.g. Kanpur', 'state': 'e.g. Uttar Pradesh',
                        'pincode': '6-digit pincode',
                        'description': 'Describe the problem in a few words'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])
            if name in placeholders:
                field.widget.attrs['placeholder'] = tr(placeholders[name])
        for name in ('address', 'city', 'state', 'pincode'):
            self.fields[name].required = True
        self.fields['pincode'].widget.attrs['inputmode'] = 'numeric'
        cat = self.fields['category']
        cat.widget.attrs['class'] = 'form-select'
        cat.choices = [('', tr('Select category'))] + [
            (value, tr(label)) for value, label in Complaint.CATEGORY_CHOICES]
        self.fields['image'].required = True

    def clean_area(self):
        return self.cleaned_data['area'].strip().title()

    def clean_city(self):
        return self.cleaned_data['city'].strip().title()

    def clean_state(self):
        return self.cleaned_data['state'].strip().title()

    def clean_pincode(self):
        return _validate_pincode(self.cleaned_data['pincode'])


class CleaningForm(forms.Form):
    """Collector uploads this once the place is clean."""
    image = forms.ImageField()
    note = forms.CharField(required=False, max_length=500)

    def clean_image(self):
        image = self.cleaned_data['image']
        if image.size > 8 * 1024 * 1024:
            raise forms.ValidationError(tr('Photo is too large. Maximum size is 8 MB.'))
        return image
