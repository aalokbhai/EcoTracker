"""Shared approval -> clean -> verify workflow used by complaints AND pickup requests.

Status flow
-----------
pending      citizen submitted, waiting for the MC office
rejected     MC office cancelled it (a reason is always stored)
approved     MC office approved it; visible to garbage collectors
in_progress  a collector accepted it and is on the way / cleaning
cleaned      collector uploaded the "after" photo; waiting for MC check
resolved     MC office verified the cleaning (counts as cleaned for the collector)
cancelled    citizen withdrew a pending request
"""
from urllib.parse import quote_plus

from django.conf import settings
from django.db import models

WORKFLOW_STATUSES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('in_progress', 'In Progress'),
    ('cleaned', 'Awaiting Verification'),
    ('resolved', 'Resolved'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]

EVENT_CHOICES = [
    ('approved', 'Approved by MC office'),
    ('rejected', 'Rejected by MC office'),
    ('assigned', 'Assigned to a collector'),
    ('accepted', 'Collector started the work'),
    ('cleaned', 'Cleaning photo uploaded'),
    ('verified', 'Cleaning verified by MC office'),
    ('redo', 'Sent back for re-cleaning'),
    ('cancelled', 'Cancelled by citizen'),
]

STEP_ORDER = ['pending', 'approved', 'in_progress', 'cleaned', 'resolved']
STEP_LABELS = [
    ('Submitted', 'bi-send'),
    ('Approved by MC office', 'bi-patch-check'),
    ('Collector working on it', 'bi-truck'),
    ('Cleaned, awaiting MC check', 'bi-camera'),
    ('Resolved', 'bi-check2-circle'),
]


class WorkflowBase(models.Model):
    status = models.CharField(max_length=20, choices=WORKFLOW_STATUSES, default='pending')

    # Full postal address (street/landmark + area live on the concrete models)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    pincode = models.CharField(max_length=6, blank=True)

    # Step 1 - MC office review
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Step 2 - garbage collector
    collector = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='assigned_%(class)ss')
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)

    # Step 3 - proof of cleaning
    after_image = models.ImageField(upload_to='cleaned/', null=True, blank=True)
    after_ai_score = models.FloatField(null=True, blank=True)   # AI "waste still visible" % on the after photo
    collector_note = models.TextField(blank=True)
    cleaned_at = models.DateTimeField(null=True, blank=True)

    # Step 4 - MC office verifies the cleaning
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')
    verified_at = models.DateTimeField(null=True, blank=True)
    redo_reason = models.TextField(blank=True)

    class Meta:
        abstract = True

    STATUS_CHOICES = WORKFLOW_STATUSES

    # ---- address helpers -------------------------------------------------
    @property
    def full_address(self):
        parts = [getattr(self, 'address', ''), getattr(self, 'area', ''),
                 self.city, self.state, self.pincode]
        return ', '.join(p.strip() for p in parts if p and p.strip())

    @property
    def maps_directions_url(self):
        """Opens Google Maps with turn-by-turn directions from the user's location."""
        return ('https://www.google.com/maps/dir/?api=1&travelmode=driving&destination='
                + quote_plus(self.full_address))

    @property
    def maps_embed_url(self):
        return 'https://maps.google.com/maps?output=embed&q=' + quote_plus(self.full_address)

    # ---- state helpers ---------------------------------------------------
    @property
    def is_closed(self):
        return self.status in ('resolved', 'rejected', 'cancelled')

    @property
    def progress_steps(self):
        """Stepper for the citizen/officer pages: done / active / waiting."""
        if self.status in ('rejected', 'cancelled'):
            current = 0
        else:
            current = STEP_ORDER.index(self.status)
        steps = []
        for i, (label, icon) in enumerate(STEP_LABELS):
            if i <= current:
                state = 'done'
            elif i == current + 1 and self.status not in ('rejected', 'cancelled'):
                state = 'active'
            else:
                state = ''
            steps.append({'label': label, 'icon': icon, 'state': state})
        return steps
