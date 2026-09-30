from django import forms

from accounts.i18n import tr

from .models import Feedback, FeedbackReply

MAX_PHOTO_MB = 3


class FeedbackForm(forms.ModelForm):
    # Rendered as clickable stars in the template; validated here.
    rating = forms.TypedChoiceField(
        choices=[(i, str(i)) for i in range(5, 0, -1)],
        coerce=int,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Feedback
        fields = ['rating', 'message', 'photo']
        widgets = {'message': forms.Textarea(attrs={'rows': 4, 'maxlength': 1000})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'rating': 'Your rating', 'message': 'Your comment', 'photo': 'Photo (optional)'}
        for name, field in self.fields.items():
            field.label = tr(labels[name])
            if name != 'rating':
                field.widget.attrs['class'] = 'form-control'
        self.fields['rating'].error_messages['required'] = tr('Please select a star rating.')
        self.fields['rating'].error_messages['invalid_choice'] = tr('Please select a star rating.')
        self.fields['message'].widget.attrs['placeholder'] = tr('Share your experience with EcoTrack')

    def clean_message(self):
        return self.cleaned_data['message'].strip()

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > MAX_PHOTO_MB * 1024 * 1024:
            raise forms.ValidationError(tr('Photo is too large. Maximum size is 3 MB.'))
        return photo


class ReplyForm(forms.ModelForm):
    class Meta:
        model = FeedbackReply
        fields = ['message']
        widgets = {'message': forms.Textarea(attrs={'rows': 2, 'maxlength': 500})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['message']
        field.label = tr('Reply')
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = tr('Write a reply...')

    def clean_message(self):
        return self.cleaned_data['message'].strip()
