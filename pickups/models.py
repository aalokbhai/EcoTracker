from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from complaints.workflow import WorkflowBase


class PickupRequest(WorkflowBase):
    WASTE_TYPE_CHOICES = [
        ('wet', 'Wet Waste'),
        ('dry', 'Dry Waste'),
        ('recyclable', 'Recyclable'),
        ('hazardous', 'Hazardous'),
        ('ewaste', 'E-Waste'),
    ]
    kind = 'pickup'
    kind_label = 'Pickup'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickups')
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPE_CHOICES)
    area = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255)
    preferred_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pickup #{self.id} - {self.get_waste_type_display()}"

    @property
    def title(self):
        return self.get_waste_type_display()

    @property
    def before_image(self):
        return None

    def get_absolute_url(self):
        return reverse('pickup_detail', args=[self.pk])
