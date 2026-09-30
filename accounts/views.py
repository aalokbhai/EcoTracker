from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from complaints.models import Complaint
from feedback.models import Feedback

from .forms import LoginForm, RegisterForm
from .i18n import tr
from .models import Profile
from .roles import home_url_name


def home(request):
    visible_feedback = Feedback.objects.filter(is_visible=True)
    context = {
        # random comments for the moving "train" slider on the home page
        'testimonials': visible_feedback.order_by('?')[:10],
        'total': Complaint.objects.count(),
        'pending': Complaint.objects.filter(status='pending').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
    }
    return render(request, 'home.html', context)


class RoleLoginView(LoginView):
    """Login page that sends each role to its own workspace."""
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse(home_url_name(self.request.user))


@login_required
def post_login(request):
    return redirect(home_url_name(request.user))


def register(request):
    if request.user.is_authenticated:
        return redirect(home_url_name(request.user))
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.profile.role == Profile.ROLE_COLLECTOR:
                messages.info(request, tr('Account created. The MC office will approve your collector account shortly.'))
            else:
                messages.success(request, tr('Your account has been created. Welcome!'))
            return redirect(home_url_name(user))
    else:
        form = RegisterForm(initial={'role': request.GET.get('role', Profile.ROLE_CITIZEN)})
    return render(request, 'registration/register.html', {'form': form})


def set_language(request, code):
    target = request.META.get('HTTP_REFERER', '')
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        target = reverse('home')
    response = redirect(target)
    if code in ('en', 'hi'):
        response.set_cookie('lang', code, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return response
