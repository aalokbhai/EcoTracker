from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.views.decorators.http import require_POST

from .models import Complaint
from pickups.models import PickupRequest


def staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))


@staff_required
def dashboard(request):
    stats = {
        'total': Complaint.objects.count(),
        'pending': Complaint.objects.filter(status='pending').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
        'review': Complaint.objects.filter(ai_verified=False).count(),
        'pickups': PickupRequest.objects.filter(status='pending').count(),
    }
    stats['rate'] = round(stats['resolved'] * 100 / stats['total']) if stats['total'] else 0

    area_qs = (Complaint.objects.values('area')
               .annotate(count=Count('id')).order_by('-count')[:8])
    cat_map = dict(Complaint.CATEGORY_CHOICES)
    cat_qs = (Complaint.objects.values('category')
              .annotate(count=Count('id')).order_by('category'))

    context = {
        'stats': stats,
        'area_labels': [a['area'] for a in area_qs],
        'area_counts': [a['count'] for a in area_qs],
        'cat_labels': [cat_map.get(c['category'], c['category']) for c in cat_qs],
        'cat_counts': [c['count'] for c in cat_qs],
        'recent': Complaint.objects.select_related('user')[:5],
    }
    return render(request, 'manage/dashboard.html', context)


@staff_required
def manage_complaints(request):
    qs = Complaint.objects.select_related('user')

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
    }
    return render(request, 'manage/complaints.html', context)


@staff_required
@require_POST
def update_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    status = request.POST.get('status')
    if status in dict(Complaint.STATUS_CHOICES):
        complaint.status = status
    complaint.admin_remark = request.POST.get('admin_remark', '').strip()
    complaint.save()
    messages.success(request, f'Complaint #{complaint.id} Updated ')
    return redirect('manage_complaints')


@staff_required
def manage_pickups(request):
    context = {
        'pickups': PickupRequest.objects.select_related('user'),
        'status_choices': PickupRequest.STATUS_CHOICES,
    }
    return render(request, 'manage/pickups.html', context)


@staff_required
@require_POST
def update_pickup(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk)
    status = request.POST.get('status')
    if status in dict(PickupRequest.STATUS_CHOICES):
        pickup.status = status
        pickup.save(update_fields=['status'])
        messages.success(request, f'Pickup #{pickup.id} Updated')
    return redirect('manage_pickups')