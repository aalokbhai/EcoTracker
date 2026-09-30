from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from feedback.models import Feedback, FeedbackReply

# (name, rating, message, days_ago)
FEEDBACKS = [
    ('Ananya Gupta', 5,
     'EcoTrack made reporting garbage so easy. I uploaded a photo in under a minute and the team '
     'cleared the spot the very next day. Excellent work!', 12),
    ('Vikram Singh', 5,
     'The status tracking is brilliant. I could see my complaint move from Pending to Resolved '
     'without calling anyone. Very transparent.', 10),
    ('Priya Verma', 4,
     'Clean design and very simple to use, even for my parents. The Hindi option is a great touch '
     'for our neighbourhood.', 9),
    ('Amit Tiwari', 5,
     'Requested a pickup for e-waste and it was collected on the exact date I chose. '
     'Finally a platform that actually works!', 8),
    ('Sneha Mishra', 5,
     'The awareness section taught me how to segregate wet and dry waste properly. '
     'Our whole society follows it now. Thank you, EcoTrack!', 6),
    ('Rahul Yadav', 4,
     'Love the AI photo check. It keeps fake reports out, so genuine complaints get attention faster. '
     'Really smart idea.', 5),
    ('कविता दुबे', 5,
     'बहुत बढ़िया प्लेटफ़ॉर्म है! हमारे मोहल्ले की सड़क की सफ़ाई दो दिन में हो गई। '
     'सभी को इसका इस्तेमाल करना चाहिए।', 3),
    ('मोहित श्रीवास्तव', 5,
     'शिकायत दर्ज करना बहुत आसान है और हर अपडेट तुरंत दिखता है। '
     'टीम का काम काबिले-तारीफ़ है।', 1),
]

# (index of feedback, reply author, is_team, message)
REPLIES = [
    (0, 'EcoTrack Team', True,
     'Thank you so much, Ananya! Your report helped us act quickly. Keep helping keep the city clean.'),
    (2, 'Ananya Gupta', False,
     'Agree with you, Priya. The Hindi option really helps everyone in the family.'),
    (4, 'EcoTrack Team', True,
     'That is wonderful to hear, Sneha! Small habits at home make a big difference.'),
]


class Command(BaseCommand):
    help = 'Adds 8 positive demo comments (with ratings) and a few replies. Safe to run many times.'

    def handle(self, *args, **options):
        now = timezone.now()
        created = []
        for name, rating, message, days_ago in FEEDBACKS:
            fb, is_new = Feedback.objects.get_or_create(
                name=name, message=message, defaults={'rating': rating})
            if is_new:
                # auto_now_add ignores values on create, so set the date afterwards
                Feedback.objects.filter(pk=fb.pk).update(
                    created_at=now - timedelta(days=days_ago, hours=days_ago))
            created.append((fb, is_new))

        for idx, name, is_team, message in REPLIES:
            fb = created[idx][0]
            FeedbackReply.objects.get_or_create(
                feedback=fb, name=name, message=message, defaults={'is_team': is_team})

        new_count = sum(1 for _, is_new in created if is_new)
        self.stdout.write(self.style.SUCCESS(
            f'Done. {new_count} new feedback added, {len(created) - new_count} already existed.'))
