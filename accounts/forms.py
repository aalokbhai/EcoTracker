from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .i18n import tr


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'username': 'Username', 'email': 'Email',
                  'password1': 'Password', 'password2': 'Confirm password'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'username': 'Username', 'password': 'Password'}
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.label = tr(labels[name])