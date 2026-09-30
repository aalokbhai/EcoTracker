from django.contrib import admin

from .models import ActivityLog, Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'area', 'city', 'status', 'collector', 'ai_verified', 'created_at')
    list_filter = ('status', 'category', 'city', 'area')
    search_fields = ('area', 'address', 'city', 'pincode', 'user__username')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('kind', 'object_id', 'event', 'status', 'actor', 'created_at')
    list_filter = ('kind', 'event')
