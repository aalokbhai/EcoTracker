from django.core.management.base import BaseCommand

from awareness.models import AwarenessArticle

ARTICLES = [
    ('segregation', 'Why segregate waste at source?',
     'Separating waste at home makes recycling possible and reduces what goes to landfills.\n\n'
     'Keep two bins: green for wet waste (food scraps, peels) and blue for dry waste (paper, plastic, metal, glass).',
     'कचरा घर पर ही अलग-अलग क्यों करें?',
     'घर पर ही कचरा अलग करने से रीसाइक्लिंग आसान होती है और कूड़े के ढेर में कम कचरा जाता है।\n\n'
     'दो डस्टबिन रखें: हरा डिब्बा गीले कचरे (सब्ज़ी-फल के छिलके, बचा खाना) के लिए और नीला डिब्बा सूखे कचरे (कागज़, प्लास्टिक, धातु, काँच) के लिए।'),
    ('segregation', 'What is wet waste vs dry waste?',
     'Wet waste is biodegradable: kitchen scraps, vegetable peels, leaves and flowers.\n\n'
     'Dry waste does not rot: plastic, paper, cardboard, metal, glass and rubber. Never mix the two in one bag.',
     'गीला कचरा और सूखा कचरा क्या है?',
     'गीला कचरा वो है जो सड़कर मिट्टी में मिल जाता है: रसोई का बचा सामान, सब्ज़ियों के छिलके, पत्ते और फूल।\n\n'
     'सूखा कचरा सड़ता नहीं है: प्लास्टिक, कागज़, गत्ता, धातु, काँच और रबड़। दोनों को कभी एक ही थैली में न मिलाएं।'),
    ('recycling', 'Simple ways to recycle at home',
     'Rinse plastic bottles and containers before disposing them. Flatten cardboard boxes.\n\n'
     'Give old clothes, books and working electronics to donation drives instead of throwing them.',
     'घर पर रीसाइक्लिंग के आसान तरीके',
     'प्लास्टिक की बोतलें और डिब्बे फेंकने से पहले धो लें। गत्ते के डिब्बे चपटे करके रखें।\n\n'
     'पुराने कपड़े, किताबें और चलने वाला इलेक्ट्रॉनिक सामान फेंकने की जगह ज़रूरतमंदों को दान करें।'),
    ('recycling', 'Turn kitchen waste into compost',
     'Wet waste can be converted into compost in 30-45 days using a simple pot or bin.\n\n'
     'Layer kitchen scraps with dry leaves, keep it slightly moist and turn it weekly. Use it for plants.',
     'रसोई के कचरे से खाद बनाएं',
     'गीले कचरे से 30-45 दिन में घर पर ही खाद बन सकती है। बस एक गमला या डिब्बा चाहिए।\n\n'
     'रसोई के कचरे के ऊपर सूखे पत्ते डालें, हल्की नमी रखें और हफ्ते में एक बार मिला दें। यह खाद पौधों के लिए बहुत अच्छी होती है।'),
    ('hazardous', 'Handling hazardous waste safely',
     'Batteries, expired medicines, paint, bulbs and chemicals are hazardous. Do not mix them with regular garbage.\n\n'
     'Store them separately and hand them over to authorised collection points.',
     'खतरनाक कचरे को सुरक्षित तरीके से संभालें',
     'बैटरी, एक्सपायर दवाइयाँ, पेंट, बल्ब और केमिकल खतरनाक कचरा हैं। इन्हें आम कचरे में न मिलाएं।\n\n'
     'इन्हें अलग रखें और अधिकृत कलेक्शन पॉइंट पर जमा करें।'),
    ('hazardous', 'What to do with e-waste',
     'Old phones, chargers and laptops contain toxic metals. Never burn or dump them.\n\n'
     'Give them to authorised e-waste recyclers or manufacturer take-back programmes.',
     'ई-वेस्ट का क्या करें?',
     'पुराने फोन, चार्जर और लैपटॉप में ज़हरीली धातुएं होती हैं। इन्हें कभी जलाएं या फेंकें नहीं।\n\n'
     'इन्हें अधिकृत ई-वेस्ट रीसाइक्लर को दें या कंपनी की टेक-बैक योजना में जमा करें।'),
    ('general', 'Say no to single-use plastic',
     'Carry a cloth bag, a steel bottle and your own container for takeaway.\n\n'
     'Small habits, repeated daily by many people, keep tons of plastic out of drains and roads.',
     'एक बार इस्तेमाल होने वाले प्लास्टिक को ना कहें',
     'कपड़े का थैला, स्टील की बोतल और खाना पैक कराने के लिए अपना डिब्बा साथ रखें।\n\n'
     'हर रोज़ की ये छोटी आदतें नालियों और सड़कों से टनों प्लास्टिक दूर रखती हैं।'),
    ('general', 'Report, do not ignore',
     'An overflowing bin or illegal dumping spot is a health risk. Report it with a clear photo and the exact area.\n\n'
     'Tracking your complaint helps make sure it gets resolved.',
     'अनदेखा न करें, शिकायत करें',
     'ओवरफ्लो होता डस्टबिन या कचरा फेंकने की गलत जगह सेहत के लिए खतरा है। साफ़ फोटो और सही इलाके के साथ शिकायत दर्ज करें।\n\n'
     'अपनी शिकायत को ट्रैक करते रहें ताकि वह ज़रूर हल हो।'),
]


class Command(BaseCommand):
    help = 'Adds or updates sample awareness articles (English + Hindi)'

    def handle(self, *args, **kwargs):
        for category, title, content, title_hi, content_hi in ARTICLES:
            AwarenessArticle.objects.update_or_create(
                title=title,
                defaults={'category': category, 'content': content,
                          'title_hi': title_hi, 'content_hi': content_hi})
        self.stdout.write(self.style.SUCCESS(f'{len(ARTICLES)} articles ready.'))