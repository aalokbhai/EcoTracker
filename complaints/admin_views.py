"""MC office (officer) pages: dashboard, review queues and collector management."""
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.i18n import tr
from accounts.roles import COLLECTOR, officer_required
from pickups.models import PickupRequest

from .models import Complaint
from .services import collector_stats

staff_required = officer_required   # kept for backwards compatibility


def _queue_items(limit=8):
    """Complaints and pickups that need an MC decision: new ones and cleaning proofs."""
    items = []
    for M in (Complaint, PickupRequest):
        items += list(M.objects.filter(status__in=['pending', 'cleaned']).select_related('user'))
    items.sort(key=lambda o: o.created_at)
    return items[:limit]


@officer_required
def dashboard(request):
    C, P = Complaint.objects, PickupRequest.objects
    stats = {
        'total': C.count(),
        'pending': C.filter(status='pending').count() + P.filter(status='pending').count(),
        'in_progress': (C.filter(status__in=['approved', 'in_progress']).count()
                        + P.filter(status__in=['approved', 'in_progress']).count()),
        'verify': C.filter(status='cleaned').count() + P.filter(status='cleaned').count(),
        'resolved': C.filter(status='resolved').count(),
        'review': C.filter(ai_verified=False).count(),
        'pickups': P.exclude(status__in=['resolved', 'rejected', 'cancelled']).count(),
        'collectors_waiting': User.objects.filter(profile__role=COLLECTOR, profile__is_approved=False).count(),
    }
    stats['rate'] = round(stats['resolved'] * 100 / stats['total']) if stats['total'] else 0

    area_qs = (C.values('area').annotate(count=Count('id')).order_by('-count')[:8])
    cat_map = dict(Complaint.CATEGORY_CHOICES)
    cat_qs = (C.values('category').annotate(count=Count('id')).order_by('category'))

    context = {
        'stats': stats,
        'area_labels': [a['area'] for a in area_qs],
        'area_counts': [a['count'] for a in area_qs],
        'cat_labels': [tr(cat_map.get(c['category'], c['category'])) for c in cat_qs],
        'cat_counts': [c['count'] for c in cat_qs],
        'queue': _queue_items(),
        'recent': Complaint.objects.select_related('user')[:5],
    }
    return render(request, 'manage/dashboard.html', context)


@officer_required
def manage_complaints(request):
    qs = Complaint.objects.select_related('user', 'collector')

    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    area = request.GET.get('area', '').strip()
    review = request.GET.get('review', '')

    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    if area:
        qs = qs.filter(area__icontains=area)
    if review == '1':
        qs = qs.filter(ai_verified=False)

    context = {
        'complaints': qs,
        'status_choices': Complaint.STATUS_CHOICES,
        'category_choices': Complaint.CATEGORY_CHOICES,
        'f': {'status': status, 'category': category, 'area': area, 'review': review},
        'count_pending': Complaint.objects.filter(status='pending').count(),
        'count_verify': Complaint.objects.filter(status='cleaned').count(),
    }
    return render(request, 'manage/complaints.html', context)


@officer_required
def manage_pickups(request):
    qs = PickupRequest.objects.select_related('user', 'collector')
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    context = {
        'pickups': qs,
        'status_choices': PickupRequest.STATUS_CHOICES,
        'f': {'status': status},
        'count_pending': PickupRequest.objects.filter(status='pending').count(),
        'count_verify': PickupRequest.objects.filter(status='cleaned').count(),
    }
    return render(request, 'manage/pickups.html', context)


@officer_required
def manage_collectors(request):
    collectors = (User.objects.filter(profile__role=COLLECTOR)
                  .select_related('profile').order_by('profile__is_approved', 'first_name', 'username'))
    rows = []
    for user in collectors:
        rows.append({'user': user, 'stats': collector_stats(user)})
    return render(request, 'manage/collectors.html', {'rows': rows})


@officer_required
@require_POST
def set_collector_approval(request, pk):
    user = get_object_or_404(User, pk=pk, profile__role=COLLECTOR)
    approve = request.POST.get('approve') == '1'
    user.profile.is_approved = approve
    user.profile.save(update_fields=['is_approved'])
    name = user.get_full_name().strip() or user.username
    if approve:
        messages.success(request, tr('Collector {name} approved.').format(name=name))
    else:
        messages.info(request, tr('Collector {name} suspended.').format(name=name))
    return redirect('manage_collectors')
