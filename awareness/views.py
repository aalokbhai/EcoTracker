from django.shortcuts import render
from .models import AwarenessArticle


def awareness_list(request):
    current = request.GET.get('category', '')
    articles = AwarenessArticle.objects.all()
    if current:
        articles = articles.filter(category=current)
    return render(request, 'awareness/list.html', {
        'articles': articles,
        'categories': AwarenessArticle.CATEGORY_CHOICES,
        'current': current,
    })