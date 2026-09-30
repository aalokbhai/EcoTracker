from django.contrib import admin
from .models import Complaint

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'area', 'status', 'ai_verified', 'created_at')
    list_filter = ('status', 'category', 'area')