from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from complaints.models import Complaint

from .forms import RegisterForm
from .i18n import tr


def home(request):
    context = {
        'total': Complaint.objects.count(),
        'pending': Complaint.objects.filter(status='pending').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
    }
    return render(request, 'home.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, tr('Your account has been created. Welcome!'))
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def set_language(request, code):
    target = request.META.get('HTTP_REFERER', '')
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        target = reverse('home')
    response = redirect(target)
    if code in ('en', 'hi'):
        response.set_cookie('lang', code, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return response