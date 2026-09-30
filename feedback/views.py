from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.i18n import tr

from .forms import FeedbackForm, ReplyForm
from .models import Feedback, FeedbackReply

PAGE_SIZE = 6


def _display_name(user):
    return user.get_full_name().strip() or user.username


def feedback_list(request):
    """Public page: everyone can read; only logged-in users can post."""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={reverse('feedback')}")
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.user = request.user
            fb.name = _display_name(request.user)
            fb.save()
            messages.success(request, tr('Thank you! Your feedback has been posted.'))
            return redirect('feedback')
    else:
        form = FeedbackForm()

    visible = Feedback.objects.filter(is_visible=True)
    stats = visible.aggregate(avg=Avg('rating'), total=Count('id'))
    total = stats['total']
    counts = {row['rating']: row['c']
              for row in visible.order_by().values('rating').annotate(c=Count('id'))}
    breakdown = [{'star': s, 'count': counts.get(s, 0),
                  'pct': round(counts.get(s, 0) * 100 / total) if total else 0}
                 for s in (5, 4, 3, 2, 1)]

    replies = FeedbackReply.objects.filter(is_visible=True)
    page_obj = Paginator(
        visible.prefetch_related(Prefetch('replies', queryset=replies)), PAGE_SIZE
    ).get_page(request.GET.get('page'))

    avg = round(stats['avg'] or 0, 1)
    return render(request, 'feedback/list.html', {
        'form': form,
        'reply_form': ReplyForm(),
        'page_obj': page_obj,
        'total': total,
        'avg': avg,
        'avg_stars': round(avg),
        'breakdown': breakdown,
    })


@login_required
@require_POST
def add_reply(request, pk):
    fb = get_object_or_404(Feedback, pk=pk, is_visible=True)
    form = ReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.feedback = fb
        reply.user = request.user
        reply.name = _display_name(request.user)
        reply.is_team = request.user.is_staff
        reply.save()
        messages.success(request, tr('Your reply has been posted.'))
    else:
        messages.error(request, tr('Please write a reply before sending.'))

    url = reverse('feedback')
    page = request.POST.get('page', '')
    if page.isdigit():
        url += f'?page={page}'
    return redirect(f'{url}#fb-{fb.pk}')
