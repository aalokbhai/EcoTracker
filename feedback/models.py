from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Feedback(models.Model):
    """A public comment with a star rating and an optional photo."""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='feedbacks')
    name = models.CharField(max_length=80)          # display name (kept even if the user is deleted)
    message = models.TextField(max_length=1000)
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    photo = models.ImageField(upload_to='feedback/', blank=True, null=True)
    is_visible = models.BooleanField(default=True, help_text='Untick to hide this comment from the website.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'feedback'

    def __str__(self):
        return f'{self.name} ({self.rating}/5): {self.message[:40]}'


class FeedbackReply(models.Model):
    """A comment on someone else's feedback post."""

    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='feedback_replies')
    name = models.CharField(max_length=80)
    message = models.TextField(max_length=500)
    is_team = models.BooleanField(default=False)    # True when an admin/staff member replies
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'feedback replies'

    def __str__(self):
        return f'{self.name} on #{self.feedback_id}: {self.message[:40]}'
