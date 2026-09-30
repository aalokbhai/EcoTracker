from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title