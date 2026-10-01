"""Wipe all complaints / pickups / feedback and fill the site with a realistic demo set.

    python manage.py seed_showcase            # asks for confirmation first
    python manage.py seed_showcase --yes      # no question asked
    python manage.py seed_showcase --yes --no-ai   # do not call Gemini for the AI badges

What it does
  * deletes every Complaint, PickupRequest, Feedback, reply and timeline entry (+ their photo files)
  * keeps all user accounts and the awareness articles
  * creates 20 complaints (all statuses), 7 pickup requests and 8 feedback posts with photos
  * if GEMINI_API_KEY is set, the AI badges are REAL: every photo is checked by Gemini
    (nothing is faked; with --no-ai the badges show "Not checked")

Photos
  Put your own photos in   seed_photos/before/*.jpg   (garbage)   and   seed_photos/after/*.jpg   (cleaned place)
  and they are used first. Without them, variations of the 4 sample photos in seed_assets/ are used.
"""
import shutil
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from PIL import Image, ImageEnhance, ImageOps

from accounts.models import Profile
from complaints import ai
from complaints.models import ActivityLog, Complaint
from feedback.models import Feedback, FeedbackReply
from pickups.models import PickupRequest

ROOT = Path(settings.BASE_DIR)
ASSETS = ROOT / 'seed_assets'
CUSTOM = ROOT / 'seed_photos'
CITY, STATE = 'Kanpur', 'Uttar Pradesh'

# ------------------------------------------------------------------ photos
# (asset, crop box as fractions, mirror?, brightness, colour, warm/cool shift)
BEFORE_RECIPES = [
    ('dumpster', (0, 0, 1, .62), 0, 1.0, 1.0, 0), ('green_bins', (0, .1, .6, 1), 0, 1.0, 1.0, 0),
    ('landfill', (.38, .2, 1, 1), 0, 1.0, 1.0, 0), ('road_litter', (0, 0, 1, 1), 0, 1.0, 1.0, 0),
    ('dumpster', (0, .15, 1, .8), 1, 1.0, 1.0, 0), ('green_bins', (.4, .1, 1, 1), 1, 1.0, 1.0, 0),
    ('landfill', (.38, .3, 1, 1), 1, 1.05, 1.0, 0), ('road_litter', (.1, 0, 1, .9), 1, 1.0, 1.0, 0),
    ('dumpster', (.05, .05, .95, .7), 0, 1.05, 1.05, 8), ('green_bins', (0, 0, 1, 1), 0, 1.0, 1.0, 0),
    ('landfill', (.42, .25, 1, .95), 0, 1.0, 1.1, 0), ('road_litter', (0, .2, .9, 1), 0, 1.0, 1.0, -6),
    ('dumpster', (0, 0, 1, 1), 1, 1.0, 1.0, 0), ('green_bins', (.15, .05, .85, .95), 1, 1.0, 1.0, -8),
    ('landfill', (.38, .1, 1, 1), 0, 1.1, 1.0, 8), ('dumpster', (.1, 0, .9, .55), 0, 1.0, 1.05, -6),
    ('green_bins', (.3, 0, 1, .9), 0, 1.05, 1.0, 8), ('landfill', (.38, .2, .95, 1), 1, 1.0, 1.1, 0),
    ('dumpster', (0, .3, 1, .9), 0, 1.0, 1.0, 6), ('green_bins', (0, .2, .7, .95), 1, 1.0, 1.0, 0),
]
AFTER_RECIPES = [        # clean ground / bin base / treeline cut out of the sample photos
    ('dumpster', (0, .5, 1, 1), 0, 1.0, 1.0, 0), ('landfill', (.4, .36, 1, .68), 0, 1.0, 1.0, 0),
    ('dumpster', (0, .5, 1, 1), 1, 1.05, 1.0, 6), ('landfill', (.4, .36, 1, .68), 1, 1.1, 1.0, 0),
    ('dumpster', (.1, .52, 1, 1), 0, 1.0, 1.05, -6), ('landfill', (.5, .38, 1, .68), 0, 1.05, 1.0, 6),
]


def _jpeg(img, width=1000):
    img = img.convert('RGB')
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    elif img.width < 700:                                         # tiny sample photo: enlarge a little
        img = img.resize((700, round(img.height * 700 / img.width)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, 'JPEG', quality=88)
    return buf.getvalue()


def _variant(recipe):
    name, box, flip, bright, colour, shift = recipe
    path = next(ASSETS.glob(f'{name}.*'))
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    w, h = im.size
    im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    if flip:
        im = ImageOps.mirror(im)
    im = ImageEnhance.Brightness(im).enhance(bright)
    im = ImageEnhance.Color(im).enhance(colour)
    if shift:                                                      # slightly warmer (+) or cooler (-)
        r, g, b = im.split()
        r = r.point(lambda v: max(0, min(255, v + shift)))
        b = b.point(lambda v: max(0, min(255, v - shift)))
        im = Image.merge('RGB', (r, g, b))
    return _jpeg(im)


def _custom(sub):
    folder = CUSTOM / sub
    files = sorted(p for p in folder.glob('*') if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')) \
        if folder.is_dir() else []
    return [_jpeg(ImageOps.exif_transpose(Image.open(p))) for p in files]


class Photos:
    def __init__(self):
        self.before = _custom('before') or [_variant(r) for r in BEFORE_RECIPES]
        self.after = _custom('after') or [_variant(r) for r in AFTER_RECIPES]
        self.custom = bool(_custom('before'))

    def get_before(self, i):
        return self.before[i % len(self.before)]

    def get_after(self, i):
        return self.after[i % len(self.after)]


# -------------------------------------------------------------------- data
# days_ago, category, area, pincode, address, description, plan, photo
COMPLAINTS = [
    (14, 'garbage_on_road', 'Kakadeo', '208025', 'Service road, opposite Kakadeo metro pillar 12',
     'Large pile of mixed garbage on the service road near the metro pillar. It has been spreading onto the road '
     'for a week and is blocking two-wheelers.', 'resolved'),
    (13, 'overflowing_bin', 'Swaroop Nagar', '208002', 'Near Swaroop Nagar Park gate',
     'The community dustbin outside the park has been overflowing for 4 days. Stray dogs tear the bags open and '
     'the smell is unbearable in the evening.', 'resolved'),
    (12, 'illegal_dumping', 'Panki', '208020', 'Behind Panki Power House boundary wall',
     'Construction debris and household waste are dumped here every night. Please take action and put up a '
     'warning board.', 'resolved'),
    (10, 'missed_collection', 'Govind Nagar', '208006', 'Lane 4, near Hanuman Mandir',
     'Hamari gali mein 6 din se kachre ki gaadi nahi aayi. Ghar ke bahar kachra jama ho gaya hai aur badbu aa rahi '
     'hai. Kripya jaldi safai karwayein.', 'resolved'),
    (9, 'overflowing_bin', 'Civil Lines', '208001', 'In front of Civil Lines bus stand',
     'Dustbins at the bus stand are full and plastic is flying onto the road. Hundreds of commuters use this stop '
     'every day.', 'resolved'),
    (8, 'garbage_on_road', 'Kidwai Nagar', '208011', 'Main road, near Kidwai Nagar market',
     'Vegetable market waste is thrown on the road after closing time. Rotting vegetables are attracting cows '
     'and flies.', 'resolved'),
    (6, 'garbage_on_road', 'Juhi', '208014', 'Near Juhi railway crossing',
     'Garbage lying near the railway crossing.', 'rejected:This looks like a duplicate of an earlier complaint '
     'for the same spot. Please track the existing request instead.'),
    (5, 'missed_collection', 'Nawabganj', '208002', 'Gali no. 7, behind the post office',
     'Garbage has not been collected from our lane for 5 days and it is spilling onto the main road.',
     'redo:The photo shows part of the garbage is still on the left side. Please clean the full area and upload a '
     'fresh photo.'),
    (5, 'overflowing_bin', 'Civil Lines', '208001', 'Near the clock tower',
     'Bin is full.', 'rejected:The photo does not clearly show the problem. Please upload a clear photo of the '
                     'waste and submit again.'),
    (4, 'illegal_dumping', 'Barra', '208027', 'Barra-8, near the water tank',
     'People from outside the colony dump sacks of waste near the water tank early in the morning. '
     'Please put a CCTV camera or a fine board.', 'cleaned'),
    (3, 'garbage_on_road', 'Arya Nagar', '208002', 'Arya Nagar crossing, towards Parade',
     'Garbage and broken plastic crates are spread over the road side and a cow is eating the plastic. This is '
     'dangerous for the animal and the traffic.', 'cleaned'),
    (3, 'garbage_on_road', 'Kalyanpur', '208017', 'Kalyanpur Awas Vikas road',
     'Kachre ka dher road ke kinare 3 hafte se pada hai, baarish mein nali band ho rahi hai.', 'in_progress'),
    (2, 'overflowing_bin', 'Saket Nagar', '208014', '801, W-1 Block, opposite VSIPS',
     'Dustbin near the college gate overflows daily after lunch time. Students and shopkeepers are facing a '
     'bad smell.', 'cleaned'),
    (2, 'overflowing_bin', 'Harsh Nagar', '208012', 'Harsh Nagar chauraha',
     'The large container at the crossing has not been emptied for a week; waste is lying all around it.',
     'in_progress'),
    (2, 'illegal_dumping', 'Shastri Nagar', '208005', 'Shastri Nagar, near the community hall',
     'Old furniture, mattresses and rubble were dumped on the empty plot next to the community hall.',
     'approved_assigned'),
    (1, 'missed_collection', 'Naubasta', '208021', 'Naubasta, near the government school',
     'Door-to-door collection vehicle skipped our block three times this week.', 'approved_open'),
    (1, 'garbage_on_road', 'Swaroop Nagar', '208002', 'Swaroop Nagar, near the Sunday market',
     'After the Sunday market a big heap of waste is left on the road. It is still there on Tuesday.', 'pending'),
    (1, 'overflowing_bin', 'Govind Nagar', '208006', 'Govind Nagar, near the vegetable market',
     'Green dustbins are overflowing and the waste has spread onto the footpath. Please send a collection van '
     'today.', 'pending'),
    (0, 'illegal_dumping', 'Kakadeo', '208025', 'Kakadeo, behind the petrol pump',
     'Someone is burning waste behind the petrol pump every night. The smoke is very harmful for the nearby '
     'houses and is a fire risk.', 'pending'),
    (0, 'missed_collection', 'Juhi', '208014', 'Juhi Kala, lane near the Shiv Mandir',
     'Kooda uthane wali gaadi aaj subah bhi nahi aayi. Kachra gali ke kone mein jama ho raha hai.', 'pending'),
]

COLLECTOR_NOTES = [
    'Garbage lifted and the place washed with the help of 2 sanitation workers.',
    'Kachra uthwa diya gaya hai aur jagah saaf kar di gayi hai.',
    'Waste removed in the municipal truck. Lime powder sprinkled on the spot.',
    'Cleaned the full stretch. Asked nearby shopkeepers to use the bins.',
    'Area swept and the container emptied completely.',
    'Debris removed with a JCB; the plot is clear now.',
]

# days_ago, waste_type, area, pincode, address, preferred offset (days from today), notes, plan
PICKUPS = [
    (9, 'dry', 'Juhi', '208014', 'House 45, Juhi Kala', -7,
     'Old newspapers and cardboard boxes after shifting house, about 10 bags.', 'resolved'),
    (4, 'ewaste', 'Saket Nagar', '208014', '801, W-1 Block, Saket Nagar', -1,
     'Old CPU, keyboards and 2 monitors from the computer lab.', 'cleaned'),
    (3, 'recyclable', 'Swaroop Nagar', '208002', 'B-12, Swaroop Nagar', 0,
     'Plastic bottles, glass jars and tin cans collected for a month.', 'in_progress'),
    (2, 'hazardous', 'Kidwai Nagar', '208011', 'Kidwai Nagar, near the dispensary', 1,
     'Expired medicines and used batteries. Please send someone who can handle them safely.',
     'approved_assigned'),
    (1, 'wet', 'Govind Nagar', '208006', 'Govind Nagar, lane 2', 1,
     'Garden waste and leaves after tree trimming, around 8 bags.', 'pending'),
    (0, 'dry', 'Civil Lines', '208001', 'Civil Lines, near the post office', 3,
     'Wooden furniture pieces and packing material, 2 big bundles.', 'pending'),
    (3, 'ewaste', 'Kakadeo', '208025', 'Kakadeo, near the metro station', -1,
     'One old refrigerator and a washing machine.',
     'rejected:The selected date is a public holiday. Please choose another date and request again.'),
]

FEEDBACK = [   # username, rating, message, days_ago
    ('itz_mansi_0', 5, 'My complaint was resolved in just 2 days! The "after" photo from the collector gave me '
                       'full confidence that the work was really done.', 6),
    ('mansi', 4, 'Hindi option bahut kaam ka hai, meri maa bhi ab complaint kar paati hain. Thanks team!', 5),
    ('hans', 5, 'Google Maps link se address dhundna bahut aasan ho gaya, rozana ka time bachta hai.', 5),
    ('aalok_miishraa', 5, 'Clean design and the whole process is easy to follow: complaint, approval, cleaning, '
                          'verification.', 4),
    ('itz_mansi_0', 4, 'AI photo check is a great idea. It would be even better with an SMS when my complaint '
                       'gets approved.', 3),
    ('mansi', 5, 'Awareness section ne mujhe sikhaya ki wet aur dry kachra alag kaise karte hain. Bahut useful.', 3),
    ('hans', 3, 'Sometimes two tasks come in the same area at the same time. A route suggestion would help.', 2),
    ('itz_mansi_0', 5, 'Pickup request for old newspapers was done on the same day. Great initiative for Kanpur!', 1),
]
REPLIES = [   # index into FEEDBACK, username, message
    (4, 'abhinav', 'Thank you! SMS/WhatsApp notifications are on our list of next features.'),
    (6, 'abhinav', 'Good suggestion. We are planning route optimisation for collectors.'),
    (0, 'mansi', 'Same experience here, the timeline view is really helpful.'),
]


def _name(u):
    return u.get_full_name().strip() or u.username


class Command(BaseCommand):
    help = 'Wipe complaints/pickups/feedback and create a demo data set with photos (see file header).'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='do not ask for confirmation')
        parser.add_argument('--no-ai', action='store_true', help='do not call Gemini (AI badges stay "Not checked")')
        parser.add_argument('--citizen', default='itz_mansi_0', help='account that owns the complaints')
        parser.add_argument('--officer', default='abhinav', help='MC officer account')
        parser.add_argument('--collector', default='hans', help='garbage collector account')

    # -------------------------------------------------------------- helpers
    def _user(self, username, label, staff=None):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'{label} account "{username}" does not exist. Use --{label.lower()} <username>.')

    def _wipe(self):
        for M in (ActivityLog, FeedbackReply, Feedback, Complaint, PickupRequest):
            M.objects.all().delete()
        for sub in ('complaints', 'cleaned', 'feedback'):
            shutil.rmtree(Path(settings.MEDIA_ROOT) / sub, ignore_errors=True)
        if connection.vendor == 'sqlite':                          # so the new complaints start at #1
            with connection.cursor() as cur:
                cur.execute("DELETE FROM sqlite_sequence WHERE name IN "
                            "('complaints_complaint','pickups_pickuprequest','feedback_feedback',"
                            "'feedback_feedbackreply','complaints_activitylog')")

    def _log(self, obj, event, status, actor, when, note=''):
        row = ActivityLog.objects.create(kind=obj.kind, object_id=obj.pk, event=event, status=status,
                                         actor=actor, note=note)
        ActivityLog.objects.filter(pk=row.pk).update(created_at=when)

    def _ai(self, path):
        if self.use_ai:
            return ai.verify_image(path)
        return None, None

    def _workflow(self, obj, plan, created, officer, collector, photos, idx):
        """Fill the workflow fields + timeline of one complaint/pickup according to its plan."""
        kind, _, reason = plan.partition(':')
        h = timedelta(hours=1)
        t_review = created + 3 * h
        t_assign = created + 4 * h
        t_start = created + 20 * h
        t_clean = created + 30 * h
        t_verify = created + 44 * h

        if kind == 'rejected':
            obj.status, obj.reviewed_by, obj.reviewed_at, obj.rejection_reason = 'rejected', officer, t_review, reason
            obj.save()
            self._log(obj, 'rejected', 'rejected', officer, t_review, reason)
            return

        if kind in ('approved_open', 'approved_assigned', 'in_progress', 'cleaned', 'resolved', 'redo'):
            obj.status, obj.reviewed_by, obj.reviewed_at = 'approved', officer, t_review
            self._log(obj, 'approved', 'approved', officer, t_review)
        if kind != 'approved_open' and kind != 'pending':
            obj.collector, obj.assigned_at = collector, t_assign
            self._log(obj, 'assigned', 'approved', officer, t_assign, _name(collector))
        if kind in ('in_progress', 'cleaned', 'resolved', 'redo'):
            obj.status, obj.started_at = 'in_progress', t_start
            self._log(obj, 'accepted', 'in_progress', collector, t_start)
        if kind in ('cleaned', 'resolved', 'redo'):
            data = photos.get_after(idx)
            obj.after_image.save(f'after_{obj.kind}_{idx + 1:02d}.jpg', ContentFile(data), save=False)
            obj.collector_note = COLLECTOR_NOTES[idx % len(COLLECTOR_NOTES)]
            obj.cleaned_at, obj.status = t_clean, 'cleaned'
            obj.save()
            _, score = self._ai(obj.after_image.path)
            obj.after_ai_score = score
            self._log(obj, 'cleaned', 'cleaned', collector, t_clean, obj.collector_note)
        if kind == 'resolved':
            obj.status, obj.verified_by, obj.verified_at = 'resolved', officer, t_verify
            self._log(obj, 'verified', 'resolved', officer, t_verify)
        if kind == 'redo':
            obj.status, obj.redo_reason = 'in_progress', reason
            self._log(obj, 'redo', 'in_progress', officer, t_clean + 4 * h, reason)
        obj.save()

    # ----------------------------------------------------------------- main
    def handle(self, *args, **opts):
        citizen = self._user(opts['citizen'], 'Citizen')
        officer = self._user(opts['officer'], 'Officer')
        collector = self._user(opts['collector'], 'Collector')
        self.use_ai = ai.is_configured() and not opts['no_ai']

        if not opts['yes']:
            self.stdout.write(self.style.WARNING(
                f'This DELETES all complaints ({Complaint.objects.count()}), pickups ({PickupRequest.objects.count()}) '
                f'and feedback ({Feedback.objects.count()}) and their photos. User accounts are kept.'))
            if input('Type YES to continue: ').strip() != 'YES':
                raise CommandError('Cancelled - nothing was changed.')

        photos = Photos()
        self.stdout.write('Photos: ' + ('your own from seed_photos/' if photos.custom
                                        else f'{len(photos.before)} sample variations'))
        self.stdout.write('AI check: ' + ('ON (real Gemini answers, takes ~1 minute)' if self.use_ai
                                          else 'OFF (badges will show "Not checked")'))
        self._wipe()

        profile = citizen.profile
        profile.city, profile.state = profile.city or CITY, profile.state or STATE
        profile.pincode = profile.pincode or '208014'
        profile.save()

        now = timezone.now()
        base = {'city': CITY, 'state': STATE}

        # ---- complaints (oldest first, so ids grow with time)
        order = sorted(range(len(COMPLAINTS)), key=lambda i: -COMPLAINTS[i][0])
        done_after = 0
        for n, i in enumerate(order):
            days, cat, area, pin, addr, desc, plan = COMPLAINTS[i]
            created = now - timedelta(days=days, hours=2 + (n * 5) % 9)
            c = Complaint(user=citizen, category=cat, area=area, pincode=pin, address=addr, description=desc,
                          **base)
            c.image.save(f'{area.lower().replace(" ", "_")}_{n + 1:02d}.jpg', ContentFile(photos.get_before(n)),
                         save=False)
            c.save()
            c.ai_verified, c.ai_confidence = self._ai(c.image.path)
            c.save()
            self._workflow(c, plan, created, officer, collector, photos, done_after)
            if plan.split(':')[0] in ('cleaned', 'resolved', 'redo'):
                done_after += 1
            Complaint.objects.filter(pk=c.pk).update(created_at=created, updated_at=max(
                [t for t in (c.verified_at, c.cleaned_at, c.reviewed_at, created) if t]))
            self.stdout.write(f'  complaint #{c.pk:<2} {plan.split(":")[0]:18} {area}')

        # ---- pickups
        for n, (days, wtype, area, pin, addr, off, notes, plan) in enumerate(
                sorted(PICKUPS, key=lambda p: -p[0])):
            created = now - timedelta(days=days, hours=3 + n)
            p = PickupRequest(user=citizen, waste_type=wtype, area=area, pincode=pin, address=addr,
                              preferred_date=(now + timedelta(days=off)).date(), notes=notes, **base)
            p.save()
            self._workflow(p, plan, created, officer, collector, photos, done_after + n)
            PickupRequest.objects.filter(pk=p.pk).update(created_at=created)
            self.stdout.write(f'  pickup    #{p.pk:<2} {plan.split(":")[0]:18} {area}')

        # ---- feedback
        posts = []
        for username, rating, msg, days in FEEDBACK:
            u = User.objects.filter(username=username).first()
            if not u:
                posts.append(None)
                continue
            fb = Feedback.objects.create(user=u, name=_name(u), message=msg, rating=rating)
            Feedback.objects.filter(pk=fb.pk).update(created_at=now - timedelta(days=days, hours=1))
            posts.append(fb)
        for idx, username, msg in REPLIES:
            u = User.objects.filter(username=username).first()
            if u and posts[idx]:
                r = FeedbackReply.objects.create(feedback=posts[idx], user=u, name=_name(u), message=msg,
                                                 is_team=u.is_staff)
                FeedbackReply.objects.filter(pk=r.pk).update(created_at=now - timedelta(hours=20))

        self.stdout.write(self.style.SUCCESS(
            f'Done: {Complaint.objects.count()} complaints, {PickupRequest.objects.count()} pickups, '
            f'{Feedback.objects.count()} feedback posts. Owner: {citizen.username}'))
