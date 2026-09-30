from django.contrib import admin

from .models import Feedback, FeedbackReply


class ReplyInline(admin.TabularInline):
    model = FeedbackReply
    extra = 0


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rating', 'short_message', 'has_photo', 'is_visible', 'created_at')
    list_filter = ('rating', 'is_visible')
    list_editable = ('is_visible',)
    search_fields = ('name', 'message')
    inlines = [ReplyInline]

    @admin.display(description='Comment')
    def short_message(self, obj):
        return obj.message[:60]

    @admin.display(boolean=True, description='Photo')
    def has_photo(self, obj):
        return bool(obj.photo)


@admin.register(FeedbackReply)
class FeedbackReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'feedback', 'name', 'is_team', 'is_visible', 'created_at')
    list_filter = ('is_team', 'is_visible')
