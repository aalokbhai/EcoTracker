from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse

from .i18n import tr

CITIZEN = 'citizen'
COLLECTOR = 'collector'
OFFICER = 'officer'


def get_role(user):
    """Return 'citizen' / 'collector' / 'officer' (None for anonymous users)."""
    if not user.is_authenticated:
        return None
    if user.is_staff:
        return OFFICER
    profile = getattr(user, 'profile', None)
    return profile.role if profile else CITIZEN


def is_approved_collector(user):
    if get_role(user) != COLLECTOR:
        return False
    return bool(getattr(user, 'profile', None) and user.profile.is_approved)


def home_url_name(user):
    """Where a user lands after login."""
    role = get_role(user)
    if role == OFFICER:
        return 'dashboard'
    if role == COLLECTOR:
        return 'collector_dashboard'
    return 'home'


def available_collectors():
    """Approved, active collectors (used for the assignment drop-down)."""
    return (User.objects.filter(profile__role=COLLECTOR, profile__is_approved=True, is_active=True)
            .select_related('profile').order_by('first_name', 'username'))


def role_required(*roles, approved=False):
    """Allow only the given roles. approved=True also requires an approved collector."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            role = get_role(request.user)
            if role not in roles:
                messages.error(request, tr('You do not have permission to open that page.'))
                return redirect(home_url_name(request.user))
            if approved and role == COLLECTOR and not is_approved_collector(request.user):
                messages.warning(request, tr('Your collector account is waiting for approval from the MC office.'))
                return redirect('collector_dashboard')
            return view(request, *args, **kwargs)
        return login_required(wrapper)
    return decorator


officer_required = role_required(OFFICER)
citizen_required = role_required(CITIZEN)


def collector_required(view=None, approved=False):
    deco = role_required(COLLECTOR, approved=approved)
    return deco(view) if view else deco
