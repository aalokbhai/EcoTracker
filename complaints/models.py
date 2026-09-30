from django.db import models
from django.contrib.auth.models import User


class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('overflowing_bin', 'Overflowing Bin'),
        ('garbage_on_road', 'Garbage on Road'),
        ('missed_collection', 'Missed Collection'),
        ('illegal_dumping', 'Illegal Dumping'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField()
    area = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # CNN result
    ai_verified = models.BooleanField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)

    admin_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} {self.get_category_display()} - {self.area}"