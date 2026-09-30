import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .i18n import tr
from .models import Profile


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=[
        (Profile.ROLE_CITIZEN, 'Citizen'),
        (Profile.ROLE_COLLECTOR, 'Garbage Collector'),
    ], initial=Profile.ROLE_CITIZEN)
    phone = forms.CharField(max_length=10, required=True)
    city = forms.CharField(max_length=80, required=True)
    state = forms.CharField(max_length=80, required=True)
    pincode = forms.CharField(max_length=6, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')

    field_order = ['role', 'first_name', 'username', 'email', 'phone',
                   'city', 'state', 'pincode', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'role': 'I am a', 'first_name': 'Full name', 'username': 'Username',
                  'email': 'Email', 'phone': 'Mobile number', 'city': 'City',
                  'state': 'State', 'pincode': 'Pincode',
                  'password1': 'Password', 'password2': 'Confirm password'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-select' if name == 'role' else 'form-control'
            field.label = tr(labels.get(name, field.label))
        self.fields['role'].choices = [
            (Profile.ROLE_CITIZEN, tr('Citizen')),
            (Profile.ROLE_COLLECTOR, tr('Garbage Collector')),
        ]
        self.fields['phone'].widget.attrs.update({'placeholder': '10-digit mobile number', 'inputmode': 'numeric'})
        self.fields['pincode'].widget.attrs.update({'placeholder': '6-digit pincode', 'inputmode': 'numeric'})

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(tr('An account with this email already exists.'))
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'\d{10}', phone):
            raise forms.ValidationError(tr('Enter a valid 10-digit mobile number.'))
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data['pincode'].strip()
        if not re.fullmatch(r'\d{6}', pincode):
            raise forms.ValidationError(tr('Enter a valid 6-digit pincode.'))
        return pincode

    def clean_city(self):
        return self.cleaned_data['city'].strip().title()

    def clean_state(self):
        return self.cleaned_data['state'].strip().title()

    def save(self, commit=True):
        user = super().save(commit=True)
        role = self.cleaned_data['role']
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.phone = self.cleaned_data['phone']
        profile.city = self.cleaned_data['city']
        profile.state = self.cleaned_data['state']
        profile.pincode = self.cleaned_data['pincode']
        # Collectors start unapproved; the MC office activates them.
        profile.is_approved = role != Profile.ROLE_COLLECTOR
        profile.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'username': 'Username', 'password': 'Password'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])
