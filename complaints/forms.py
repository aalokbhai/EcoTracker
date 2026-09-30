from django import forms

from accounts.i18n import tr

from .models import Complaint


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'area', 'address', 'description', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'category': 'Category', 'area': 'Area', 'address': 'Address',
                  'description': 'Description', 'image': 'Photo'}
        placeholders = {'area': 'e.g. Civil Lines',
                        'address': 'Nearby landmark or street (optional)',
                        'description': 'Describe the problem in a few words'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])
            if name in placeholders:
                field.widget.attrs['placeholder'] = tr(placeholders[name])
        cat = self.fields['category']
        cat.widget.attrs['class'] = 'form-select'
        cat.choices = [('', tr('Select category'))] + [
            (value, tr(label)) for value, label in Complaint.CATEGORY_CHOICES]
        self.fields['image'].required = True

    def clean_area(self):
        return self.cleaned_data['area'].strip().title()