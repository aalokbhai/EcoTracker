from django.contrib import admin
from .models import PickupRequest

@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'waste_type', 'preferred_date', 'status')
    list_filter = ('status', 'waste_type')