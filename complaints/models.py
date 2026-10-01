from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from .workflow import EVENT_CHOICES, WORKFLOW_STATUSES, WorkflowBase


class Complaint(WorkflowBase):
    CATEGORY_CHOICES = [
        ('overflowing_bin', 'Overflowing Bin'),
        ('garbage_on_road', 'Garbage on Road'),
        ('missed_collection', 'Missed Collection'),
        ('illegal_dumping', 'Illegal Dumping'),
    ]
    kind = 'complaint'
    kind_label = 'Complaint'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField()
    area = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)

    # AI photo check (Gemini): verdict, confidence (% chance that waste is visible) and a short reason
    ai_verified = models.BooleanField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_reason = models.CharField(max_length=300, blank=True)

    admin_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} {self.get_category_display()} - {self.area}"

    @property
    def title(self):
        return self.get_category_display()

    @property
    def before_image(self):
        return self.image

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('complaint_detail', args=[self.pk])


class ActivityLog(models.Model):
    """One row per workflow event; powers the timeline on every detail page."""

    kind = models.CharField(max_length=20)            # 'complaint' or 'pickup'
    object_id = models.PositiveIntegerField()
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    status = models.CharField(max_length=20, choices=WORKFLOW_STATUSES)
    note = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['kind', 'object_id'], name='activity_kind_obj_idx')]

    def __str__(self):
        return f"{self.kind} #{self.object_id}: {self.event}"
