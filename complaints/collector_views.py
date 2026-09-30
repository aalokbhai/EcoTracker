"""Garbage collector workspace."""
from django.shortcuts import render

from accounts.roles import collector_required, is_approved_collector
from pickups.models import PickupRequest

from .models import Complaint
from .services import collector_stats

TABS = [
    ('todo', 'My tasks'),
    ('available', 'Available'),
    ('verify', 'Awaiting verification'),
    ('done', 'Cleaned'),
]


def _merge(querysets):
    items = []
    for qs in querysets:
        items += list(qs)
    items.sort(key=lambda o: o.created_at, reverse=True)
    return items


def _tasks_for(user, tab):
    models = (Complaint, PickupRequest)
    mine = [M.objects.filter(collector=user).select_related('user') for M in models]
    if tab == 'available':
        city = getattr(user.profile, 'city', '')
        pool = []
        for M in models:
            qs = M.objects.filter(status='approved', collector__isnull=True).select_related('user')
            if city:
                qs = qs.filter(city__iexact=city)
            pool.append(qs)
        return _merge(pool)
    if tab == 'verify':
        return _merge(q.filter(status='cleaned') for q in mine)
    if tab == 'done':
        return _merge(q.filter(status='resolved') for q in mine)
    return _merge(q.filter(status__in=['approved', 'in_progress']) for q in mine)


@collector_required
def collector_dashboard(request):
    user = request.user
    approved = is_approved_collector(user)
    tab = request.GET.get('tab', 'todo')
    if tab not in dict(TABS):
        tab = 'todo'

    tasks = _tasks_for(user, tab) if approved else []
    tab_counts = {key: len(_tasks_for(user, key)) for key, _ in TABS} if approved else {}
    context = {
        'approved': approved,
        'stats': collector_stats(user),
        'tasks': tasks,
        'tab': tab,
        'tabs': [(key, label, tab_counts.get(key, 0)) for key, label in TABS],
    }
    return render(request, 'collector/dashboard.html', context)
