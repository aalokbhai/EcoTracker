"""Workflow actions shared by complaints and pickups + the context for their detail pages."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.i18n import tr
from accounts.roles import (COLLECTOR, OFFICER, available_collectors, collector_required,
                            get_role, is_approved_collector, officer_required)
from pickups.models import PickupRequest

from . import services
from .forms import CleaningForm
from .models import Complaint

MODELS = {'complaint': Complaint, 'pickup': PickupRequest}


def get_task(kind, pk):
    try:
        return get_object_or_404(MODELS[kind].objects.select_related('user', 'collector'), pk=pk)
    except KeyError:
        raise Http404


def can_view(user, obj):
    role = get_role(user)
    if role == OFFICER or obj.user_id == user.pk:
        return True
    if role == COLLECTOR and is_approved_collector(user):
        # own tasks, or an approved task nobody has picked up yet
        return obj.collector_id == user.pk or (obj.status == 'approved' and obj.collector_id is None)
    return False


def load_task(request, kind, pk):
    obj = get_task(kind, pk)
    if not can_view(request.user, obj):
        raise PermissionDenied
    return obj


def build_task_context(request, obj):
    role = get_role(request.user)
    ctx = {
        'obj': obj,
        'kind': obj.kind,
        'history': services.history(obj),
        'can_navigate': role in (OFFICER, COLLECTOR),
        'is_task_collector': role == COLLECTOR and obj.collector_id == request.user.pk,
        'can_accept': (role == COLLECTOR and obj.status == 'approved'
                       and obj.collector_id in (None, request.user.pk)),
    }
    if role == OFFICER and obj.status in ('pending', 'approved'):
        ctx['collectors'] = available_collectors()
    return ctx


def _done(request, obj):
    return redirect(obj.get_absolute_url())


def _run(request, kind, pk, action, success_msg):
    """Run a service call, turning WorkflowError into a friendly message."""
    obj = get_task(kind, pk)
    try:
        action(obj)
    except services.WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, success_msg.format(id=obj.pk))
    return _done(request, obj)


def _collector_from_post(request):
    cid = request.POST.get('collector', '').strip()
    if not cid.isdigit():
        return None
    return available_collectors().filter(pk=int(cid)).first()


# ------------------------------------------------------------------ officer
@officer_required
@require_POST
def task_approve(request, kind, pk):
    collector = _collector_from_post(request)
    return _run(request, kind, pk, lambda o: services.approve(o, request.user, collector),
                tr('Request #{id} approved.'))


@officer_required
@require_POST
def task_reject(request, kind, pk):
    reason = request.POST.get('reason', '')
    return _run(request, kind, pk, lambda o: services.reject(o, request.user, reason),
                tr('Request #{id} rejected and the citizen can now see the reason.'))


@officer_required
@require_POST
def task_assign(request, kind, pk):
    collector = _collector_from_post(request)
    return _run(request, kind, pk, lambda o: services.assign(o, request.user, collector),
                tr('Request #{id} assigned to the collector.'))


@officer_required
@require_POST
def task_verify(request, kind, pk):
    return _run(request, kind, pk, lambda o: services.verify_cleaning(o, request.user),
                tr('Cleaning of request #{id} verified. Marked as resolved.'))


@officer_required
@require_POST
def task_redo(request, kind, pk):
    reason = request.POST.get('reason', '')
    return _run(request, kind, pk, lambda o: services.send_back(o, request.user, reason),
                tr('Request #{id} sent back to the collector for re-cleaning.'))


# ---------------------------------------------------------------- collector
@collector_required(approved=True)
@require_POST
def task_accept(request, kind, pk):
    obj = get_task(kind, pk)
    if not can_view(request.user, obj):
        raise PermissionDenied
    return _run(request, kind, pk, lambda o: services.accept(o, request.user),
                tr('You accepted task #{id}. Use the address link to get directions.'))


@collector_required(approved=True)
@require_POST
def task_clean(request, kind, pk):
    obj = get_task(kind, pk)
    if not can_view(request.user, obj):
        raise PermissionDenied
    form = CleaningForm(request.POST, request.FILES)
    if not form.is_valid():
        for errors in form.errors.values():
            for err in errors:
                messages.error(request, err)
        return _done(request, obj)
    try:
        services.submit_cleaning(obj, request.user, form.cleaned_data['image'], form.cleaned_data['note'])
    except services.WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, tr('Photo uploaded. The MC office will verify the cleaning.'))
    return _done(request, obj)


# ------------------------------------------------------------------- citizen
@login_required
@require_POST
def task_cancel(request, kind, pk):
    obj = get_task(kind, pk)
    try:
        services.cancel_by_owner(obj, request.user)
    except services.WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.info(request, tr('Request #{id} cancelled.').format(id=obj.pk))
    return redirect('my_pickups' if kind == 'pickup' else 'my_complaints')
