from django.core.management.base import BaseCommand
from awareness.models import AwarenessArticle

ARTICLES = [
    ('segregation', 'Why segregate waste at source?',
     'Separating waste at home makes recycling possible and reduces what goes to landfills.\n\n'
     'Keep two bins: green for wet waste (food scraps, peels) and blue for dry waste (paper, plastic, metal, glass).'),
    ('segregation', 'What is wet waste vs dry waste?',
     'Wet waste is biodegradable: kitchen scraps, vegetable peels, leaves and flowers.\n\n'
     'Dry waste does not rot: plastic, paper, cardboard, metal, glass and rubber. Never mix the two in one bag.'),
    ('recycling', 'Simple ways to recycle at home',
     'Rinse plastic bottles and containers before disposing them. Flatten cardboard boxes.\n\n'
     'Give old clothes, books and working electronics to donation drives instead of throwing them.'),
    ('recycling', 'Turn kitchen waste into compost',
     'Wet waste can be converted into compost in 30-45 days using a simple pot or bin.\n\n'
     'Layer kitchen scraps with dry leaves, keep it slightly moist and turn it weekly. Use it for plants.'),
    ('hazardous', 'Handling hazardous waste safely',
     'Batteries, expired medicines, paint, bulbs and chemicals are hazardous. Do not mix them with regular garbage.\n\n'
     'Store them separately and hand them over to authorised collection points.'),
    ('hazardous', 'What to do with e-waste',
     'Old phones, chargers and laptops contain toxic metals. Never burn or dump them.\n\n'
     'Give them to authorised e-waste recyclers or manufacturer take-back programmes.'),
    ('general', 'Say no to single-use plastic',
     'Carry a cloth bag, a steel bottle and your own container for takeaway.\n\n'
     'Small habits, repeated daily by many people, keep tons of plastic out of drains and roads.'),
    ('general', 'Report, do not ignore',
     'An overflowing bin or illegal dumping spot is a health risk. Report it with a clear photo and the exact area.\n\n'
     'Tracking your complaint helps make sure it gets resolved.'),
]


class Command(BaseCommand):
    help = 'Adds sample awareness articles'

    def handle(self, *args, **kwargs):
        created = 0
        for category, title, content in ARTICLES:
            _, is_new = AwarenessArticle.objects.get_or_create(
                title=title, defaults={'category': category, 'content': content})
            created += is_new
        self.stdout.write(self.style.SUCCESS(f'{created} articles added.'))