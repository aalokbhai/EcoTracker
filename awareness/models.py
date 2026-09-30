from django.db import models
from django.utils import translation


class AwarenessArticle(models.Model):
    CATEGORY_CHOICES = [
        ('segregation', 'Segregation'),
        ('recycling', 'Recycling'),
        ('hazardous', 'Hazardous Waste'),
        ('general', 'General Tips'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    content = models.TextField()
    title_hi = models.CharField(max_length=200, blank=True, default='')
    content_hi = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_title(self):
        if translation.get_language() == 'hi' and self.title_hi:
            return self.title_hi
        return self.title

    def get_content(self):
        if translation.get_language() == 'hi' and self.content_hi:
            return self.content_hi
        return self.content