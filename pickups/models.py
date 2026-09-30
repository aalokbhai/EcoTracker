from django.db import models
from django.contrib.auth.models import User


class PickupRequest(models.Model):
    WASTE_TYPE_CHOICES = [
        ('wet', 'Wet Waste'),
        ('dry', 'Dry Waste'),
        ('recyclable', 'Recyclable'),
        ('hazardous', 'Hazardous'),
        ('ewaste', 'E-Waste'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickups')
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPE_CHOICES)
    address = models.CharField(max_length=255)
    preferred_date = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pickup #{self.id} - {self.get_waste_type_display()}"