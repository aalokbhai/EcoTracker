from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'city', 'state', 'phone', 'is_approved', 'created_at')
    list_filter = ('role', 'is_approved', 'state')
    search_fields = ('user__username', 'user__first_name', 'phone', 'city', 'pincode')
