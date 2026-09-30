"""All state changes of the approve -> clean -> verify workflow live here.

Views only call these functions, so the rules are identical for complaints
and pickup requests and are easy to test.
"""
import logging

from django.db import transaction
from django.utils import timezone

from accounts.i18n import tr
from accounts.roles import available_collectors

from .models import ActivityLog

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Raised when an action is not allowed in the current state."""


def _log(obj, event, actor, note=''):
    ActivityLog.objects.create(kind=obj.kind, object_id=obj.pk, event=event,
                               status=obj.status, actor=actor, note=note)


def history(obj):
    return ActivityLog.objects.filter(kind=obj.kind, object_id=obj.pk).select_related('actor')


def _require_status(obj, *allowed):
    if obj.status not in allowed:
        raise WorkflowError(tr('This request is no longer in the right state for that action.'))


def _clean_collector(collector):
    if collector is None:
        return None
    if not available_collectors().filter(pk=collector.pk).exists():
        raise WorkflowError(tr('Please choose an approved garbage collector.'))
    return collector


def _name(user):
    return user.get_full_name().strip() or user.username


# ---------------------------------------------------------------- MC office
@transaction.atomic
def approve(obj, officer, collector=None):
    _require_status(obj, 'pending')
    collector = _clean_collector(collector)
    now = timezone.now()
    obj.status = 'approved'
    obj.reviewed_by, obj.reviewed_at, obj.rejection_reason = officer, now, ''
    if collector:
        obj.collector, obj.assigned_at = collector, now
    obj.save()
    _log(obj, 'approved', officer)
    if collector:
        _log(obj, 'assigned', officer, _name(collector))


@transaction.atomic
def reject(obj, officer, reason):
    reason = (reason or '').strip()
    if not reason:
        raise WorkflowError(tr('Please write the reason for rejecting this request.'))
    _require_status(obj, 'pending')
    obj.status = 'rejected'
    obj.reviewed_by, obj.reviewed_at, obj.rejection_reason = officer, timezone.now(), reason
    obj.save()
    _log(obj, 'rejected', officer, reason)


@transaction.atomic
def assign(obj, officer, collector):
    _require_status(obj, 'approved')
    collector = _clean_collector(collector)
    if collector is None:
        raise WorkflowError(tr('Please choose an approved garbage collector.'))
    obj.collector, obj.assigned_at = collector, timezone.now()
    obj.save()
    _log(obj, 'assigned', officer, _name(collector))


@transaction.atomic
def verify_cleaning(obj, officer):
    _require_status(obj, 'cleaned')
    obj.status = 'resolved'
    obj.verified_by, obj.verified_at, obj.redo_reason = officer, timezone.now(), ''
    obj.save()
    _log(obj, 'verified', officer)


@transaction.atomic
def send_back(obj, officer, reason):
    reason = (reason or '').strip()
    if not reason:
        raise WorkflowError(tr('Please write why the cleaning is not acceptable.'))
    _require_status(obj, 'cleaned')
    obj.status = 'in_progress'
    obj.redo_reason = reason
    obj.save()
    _log(obj, 'redo', officer, reason)


# ---------------------------------------------------------------- collector
@transaction.atomic
def accept(obj, collector):
    _require_status(obj, 'approved')
    if obj.collector_id and obj.collector_id != collector.pk:
        raise WorkflowError(tr('This task is assigned to another collector.'))
    now = timezone.now()
    if not obj.collector_id:
        obj.collector, obj.assigned_at = collector, now
    obj.status, obj.started_at = 'in_progress', now
    obj.save()
    _log(obj, 'accepted', collector)


@transaction.atomic
def submit_cleaning(obj, collector, image, note=''):
    _require_status(obj, 'approved', 'in_progress')
    if obj.collector_id != collector.pk:
        raise WorkflowError(tr('This task is assigned to another collector.'))
    now = timezone.now()
    obj.after_image = image
    obj.collector_note = (note or '').strip()
    obj.cleaned_at = now
    obj.started_at = obj.started_at or now
    obj.status = 'cleaned'
    obj.save()

    # Advisory AI check on the "after" photo (how much waste is still visible).
    try:
        from .ai import verify_image
        _, score = verify_image(obj.after_image.path)
        if score is not None:
            obj.after_ai_score = score
            obj.save(update_fields=['after_ai_score'])
    except Exception:
        logger.exception('After-photo AI check failed')
    _log(obj, 'cleaned', collector, obj.collector_note)


# ------------------------------------------------------------------ citizen
@transaction.atomic
def cancel_by_owner(obj, user):
    if obj.user_id != user.pk:
        raise WorkflowError(tr('You can only cancel your own requests.'))
    _require_status(obj, 'pending')
    obj.status = 'cancelled'
    obj.save()
    _log(obj, 'cancelled', user)


# -------------------------------------------------------------------- stats
def collector_stats(user):
    """How many tasks this collector has cleaned (MC-verified) and how many are still open."""
    from pickups.models import PickupRequest
    from .models import Complaint

    def count(**filters):
        return sum(M.objects.filter(collector=user, **filters).count()
                   for M in (Complaint, PickupRequest))

    cleaned = count(status='resolved')
    awaiting = count(status='cleaned')
    not_cleaned = count(status__in=['approved', 'in_progress'])
    redo = sum(M.objects.filter(collector=user, status='in_progress').exclude(redo_reason='').count()
               for M in (Complaint, PickupRequest))
    total = cleaned + awaiting + not_cleaned
    return {
        'cleaned': cleaned,
        'awaiting': awaiting,
        'not_cleaned': not_cleaned,
        'redo': redo,
        'total': total,
        'rate': round(cleaned * 100 / total) if total else 0,
    }
