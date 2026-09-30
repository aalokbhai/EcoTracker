from django.contrib import admin
from .models import PickupRequest


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'waste_type', 'city', 'preferred_date', 'status', 'collector')
    list_filter = ('status', 'waste_type', 'city')
    search_fields = ('address', 'area', 'city', 'pincode', 'user__username')
