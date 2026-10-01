"""Wipe all complaints + pickup requests and fill the site with realistic dummy data.

    python manage.py seed_complaints             # clear everything, then add demo data
    python manage.py seed_complaints --keep-old  # keep existing data, just add the demo data

Users, feedback and awareness articles are NOT touched.
"""
import random
from collections import Counter
from datetime import timedelta
from io import BytesIO, StringIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from accounts.models import Profile
from complaints.models import ActivityLog, Complaint
from pickups.models import PickupRequest

PASSWORD = 'Eco@12345'
CITY, STATE = 'Kanpur', 'Uttar Pradesh'
PINCODES = {
    'Civil Lines': '208001', 'Swaroop Nagar': '208002', 'Kakadeo': '208025',
    'Govind Nagar': '208006', 'Kidwai Nagar': '208011', 'Shastri Nagar': '208005',
    'Kalyanpur': '208017', 'Juhi': '208014', 'Saket Nagar': '208014',
    'Rawatpur': '208019', 'Harsh Nagar': '208012',
}
CITIZENS = [
    ('citizen1', 'Demo Citizen'), ('priya_sharma', 'Priya Sharma'),
    ('rahul_verma', 'Rahul Verma'), ('anita_singh', 'Anita Singh'),
]

# d = days ago, h = extra hours ago, u = citizen index, col = collector number (1/2) or None
# ai = (verified, waste probability %),  after = "waste still visible" % on the after photo
COMPLAINTS = [
    # ---- resolved ----
    dict(d=9, u=0, cat='overflowing_bin', area='Civil Lines', addr='Near Hanuman Temple, Mall Road',
         desc='The community dustbin has been overflowing for three days and stray animals are scattering the waste on the road.',
         status='resolved', col=1, ai=(True, 96.2), after=6.1,
         note='Bin emptied and the area washed. Residents were asked to keep the lid closed.'),
    dict(d=8, u=1, cat='garbage_on_road', area='Kakadeo', addr='Opposite Kakadeo Metro Station, Main Road',
         desc='A large pile of mixed garbage on the roadside is blocking the footpath and smells terrible.',
         status='resolved', col=2, ai=(True, 98.4), after=4.3,
         note='Entire pile removed and the roadside swept clean.'),
    dict(d=8, u=2, cat='illegal_dumping', area='Swaroop Nagar', addr='Vacant plot behind Park Road',
         desc='People dump construction debris and household waste in the empty plot every night.',
         status='resolved', col=1, ai=(True, 91.7), after=9.8,
         note='Debris cleared. A warning board has been requested for the plot.'),
    dict(d=7, u=3, cat='missed_collection', area='Govind Nagar', addr='Lane 4, Block B',
         desc='The garbage vehicle has not visited our lane for five days and bags are piling up outside the houses.',
         status='resolved', col=2, ai=(True, 88.5), after=5.2,
         note='Lane cleared manually and the vehicle route has been corrected.'),
    dict(d=6, u=0, cat='garbage_on_road', area='Civil Lines', addr='Near Chaman Ganj Crossing',
         desc='Garbage thrown on the road divider is spilling onto the road and causing traffic trouble.',
         status='resolved', col=1, ai=(True, 94.9), after=3.7,
         note='Divider cleaned and waste taken to the transfer station.'),
    # ---- cleaned, waiting for the MC check ----
    dict(d=5, u=1, cat='overflowing_bin', area='Kidwai Nagar', addr='Market Road, near the sweet shop',
         desc='The bin in front of the market is full and waste is lying all around it.',
         status='cleaned', col=2, ai=(True, 97.1), after=7.4,
         note='Bin emptied and the surrounding area cleaned.'),
    dict(d=4, u=2, cat='illegal_dumping', area='Kakadeo', addr='Canal bank near the Sector 7 bridge',
         desc='Plastic bags and food waste are being dumped on the canal bank and entering the water.',
         status='cleaned', col=1, ai=(True, 92.3), after=11.6,
         note='Waste collected from the bank. Please verify the water edge as well.'),
    # ---- in progress ----
    dict(d=3, u=3, cat='garbage_on_road', area='Civil Lines', addr='Outside the Government School gate',
         desc='Garbage is lying right outside the school gate and children have to walk through it.',
         status='in_progress', col=2, ai=(True, 95.8)),
    dict(d=3, u=0, cat='overflowing_bin', area='Shastri Nagar', addr='Park entrance, Sector C',
         desc='The bin near the park entrance has not been emptied for a week.',
         status='in_progress', col=1, ai=(True, 89.0), after=38.6,
         note='Main pile removed.',
         redo='Some waste is still visible near the drain. Please clean that corner as well.'),
    # ---- approved ----
    dict(d=2, u=1, cat='missed_collection', area='Kalyanpur', addr='Near Kalyanpur Railway Crossing',
         desc='Door-to-door collection has stopped in our colony since last Friday.',
         status='approved', col=2, ai=(True, 84.6)),
    dict(d=2, u=2, cat='garbage_on_road', area='Juhi', addr='Juhi Kalan Main Road',
         desc='Garbage bags have been left on the main road after the weekly market.',
         status='approved', col=None, ai=(True, 90.2)),
    # ---- pending (MC office review queue) ----
    dict(d=1, h=5, u=3, cat='overflowing_bin', area='Saket Nagar', addr='Near the institute main gate',
         desc='The dustbin at the gate is overflowing and students have to cross the waste to enter.',
         status='pending', ai=(True, 93.4)),
    dict(d=0, h=5, u=0, cat='overflowing_bin', area='Civil Lines', addr='Behind the Civil Lines bus stop',
         desc='Bin next to the bus stop is overflowing and the smell is affecting passengers.',
         status='pending', ai=(True, 93.6)),
    dict(d=0, h=2, u=1, cat='illegal_dumping', area='Kakadeo', addr='Y-Block market, back lane',
         desc='Shopkeepers are dumping their waste in the back lane instead of using the bin.',
         status='pending', ai=(True, 87.9)),
    dict(d=0, h=1, u=2, cat='garbage_on_road', area='Rawatpur', addr='Near Rawatpur Crossing',
         desc='Some garbage near the crossing, please check.',
         status='pending', ai=(False, 27.3)),
    # ---- rejected / cancelled ----
    dict(d=6, u=2, cat='illegal_dumping', area='Harsh Nagar', addr='Near the community hall',
         desc='Dumping near the hall.',
         status='rejected', ai=(False, 18.5),
         reason='The photo does not show any waste. Please upload a clear photo of the affected spot and submit again.'),
    dict(d=5, u=3, cat='overflowing_bin', area='Govind Nagar', addr='Lane 2, Block A',
         desc='The bin in our lane is overflowing again.',
         status='rejected', ai=(True, 90.1),
         reason='Duplicate of an existing complaint for the same bin that is already being handled.'),
    dict(d=4, u=1, cat='missed_collection', area='Swaroop Nagar', addr='Gali 6, near the tea stall',
         desc='Collection vehicle did not come today.',
         status='cancelled', ai=(True, 82.4)),
]

PICKUPS = [
    dict(d=8, u=0, wt='wet', area='Civil Lines', addr='House 45, near the park, Civil Lines',
         notes='Kitchen and garden waste, around 6 bags.', status='resolved', col=1, after=4.0,
         note='Collected 6 bags of wet waste.'),
    dict(d=7, u=1, wt='recyclable', area='Swaroop Nagar', addr='Flat 12, Shanti Apartments',
         notes='Clean bottles, cans and cardboard boxes after a family function.', status='resolved', col=2, after=3.2,
         note='All recyclable material collected and sent to the sorting centre.'),
    dict(d=5, u=2, wt='ewaste', area='Kidwai Nagar', addr='House 78, Block C',
         notes='Old monitor, keyboards and two broken chargers.', status='cleaned', col=1, after=5.5,
         note='E-waste collected and handed to the authorised recycler.'),
    dict(d=5, u=3, wt='hazardous', area='Kakadeo', addr='Shop 9, Y-Block market',
         notes='Expired medicines and empty paint tins.', status='in_progress', col=2),
    dict(d=3, u=0, wt='dry', area='Govind Nagar', addr='House 23, Lane 3',
         notes='Old newspapers, cartons and plastic packaging.', status='approved', col=1),
    dict(d=3, u=1, wt='wet', area='Juhi', addr='Near Juhi Sabzi Mandi',
         notes='Vegetable waste from a small stall.', status='approved', col=None),
    dict(d=2, u=2, wt='recyclable', area='Shastri Nagar', addr='House 5, Sector B',
         notes='Glass bottles and metal scrap.', status='pending'),
    dict(d=1, u=3, wt='ewaste', area='Saket Nagar', addr='Computer lab store room, near W-1 Block',
         notes='Broken keyboards, mice and old cables from the lab.', status='pending'),
    dict(d=0, h=3, u=0, wt='dry', area='Kalyanpur', addr='Flat 302, Sunrise Residency',
         notes='Packing material after moving in.', status='pending'),
    dict(d=5, u=1, wt='hazardous', area='Civil Lines', addr='House 9, Mall Road',
         notes='Old batteries and a few tube lights.', status='rejected',
         reason='Hazardous waste pickup is not available at this address. Please use the authorised collection point.'),
    dict(d=4, u=2, wt='wet', area='Rawatpur', addr='Lane 5, near the temple',
         notes='Festival leftovers.', status='cancelled'),
]


# ------------------------------------------------------------------ images
def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                      # very old Pillow
        return ImageFont.load_default()


def placeholder(kind, label, seed):
    """Simple generated photo so demo rows never look empty (kind = 'before' | 'after')."""
    rnd = random.Random(seed)
    w, h = 800, 600
    before = kind == 'before'
    img = Image.new('RGB', (w, h), (104, 98, 90) if before else (214, 236, 222))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 360, w, h], fill=(72, 68, 62) if before else (170, 200, 180))
    if before:
        palette = [(30, 30, 30), (60, 90, 60), (150, 120, 70), (180, 60, 50), (205, 205, 195), (50, 70, 120)]
        for _ in range(30):
            x, y, r = rnd.randint(40, w - 140), rnd.randint(300, 500), rnd.randint(30, 70)
            d.ellipse([x, y, x + int(r * 1.4), y + r], fill=rnd.choice(palette))
    else:
        d.line([(330, 300), (385, 355), (490, 225)], fill=(5, 150, 105), width=24)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(img)
    ink = (255, 255, 255) if before else (4, 78, 57)
    d.text((24, 20), label, fill=ink, font=_font(32))
    d.text((24, h - 46), 'Sample photo (demo data)', fill=ink, font=_font(22))
    buf = BytesIO()
    img.save(buf, 'JPEG', quality=82)
    return buf.getvalue()


def sample_pool():
    """Real photos already uploaded in media/complaints (never our own seed_ files)."""
    folder = Path(settings.MEDIA_ROOT) / 'complaints'
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir()
                  if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') and not p.name.startswith('seed_'))


def remove_old_seed_files():
    for sub in ('complaints', 'cleaned'):
        folder = Path(settings.MEDIA_ROOT) / sub
        if folder.exists():
            for p in folder.glob('seed_*'):
                p.unlink(missing_ok=True)


# ---------------------------------------------------------------- workflow
def _name(user):
    return user.get_full_name().strip() or user.username


def apply_workflow(obj, status, base, officer, collector, note='', reason='', redo=''):
    """Fill the workflow columns for the wanted final status; return the activity events."""
    limit = timezone.now() - timedelta(minutes=2)

    def at(**kw):
        return min(base + timedelta(**kw), limit)

    if status == 'pending':
        return []
    if status == 'cancelled':
        obj.status = 'cancelled'
        return [('cancelled', 'cancelled', obj.user, '', at(hours=2))]
    if status == 'rejected':
        t = at(hours=4)
        obj.status, obj.reviewed_by, obj.reviewed_at, obj.rejection_reason = 'rejected', officer, t, reason
        return [('rejected', 'rejected', officer, reason, t)]

    t = at(hours=3)
    obj.status, obj.reviewed_by, obj.reviewed_at = 'approved', officer, t
    events = [('approved', 'approved', officer, '', t)]
    if collector:
        t = at(hours=3, minutes=5)
        obj.collector, obj.assigned_at = collector, t
        events.append(('assigned', 'approved', officer, _name(collector), t))
    if status == 'approved':
        return events

    t = at(hours=20)
    obj.status, obj.started_at = 'in_progress', t
    events.append(('accepted', 'in_progress', collector, '', t))
    if status == 'in_progress' and not redo:
        return events

    t = at(days=1, hours=2)
    obj.status, obj.cleaned_at, obj.collector_note = 'cleaned', t, note
    events.append(('cleaned', 'cleaned', collector, note, t))
    if status == 'cleaned':
        return events

    if status == 'in_progress':                      # sent back for re-cleaning
        t = at(days=1, hours=8)
        obj.status, obj.redo_reason = 'in_progress', redo
        events.append(('redo', 'in_progress', officer, redo, t))
        return events

    t = at(days=1, hours=8)                          # resolved
    obj.status, obj.verified_by, obj.verified_at = 'resolved', officer, t
    events.append(('verified', 'resolved', officer, '', t))
    return events


class Command(BaseCommand):
    help = 'Delete all complaints and pickup requests, then add realistic dummy data.'

    def add_arguments(self, parser):
        parser.add_argument('--keep-old', action='store_true',
                            help='Do not delete existing complaints/pickups, only add the demo data.')

    # ------------------------------------------------------------------
    def handle(self, *args, **opts):
        with transaction.atomic():
            if not opts['keep_old']:
                c = Complaint.objects.count()
                p = PickupRequest.objects.count()
                ActivityLog.objects.all().delete()
                Complaint.objects.all().delete()
                PickupRequest.objects.all().delete()
                remove_old_seed_files()
                self.stdout.write(f'Cleared {c} complaints and {p} pickup requests.')

            officer, collectors, citizens = self.ensure_users()
            self.samples = sample_pool()

            for i, spec in enumerate(COMPLAINTS):
                self.build(Complaint, i, spec, officer, collectors, citizens)
            for i, spec in enumerate(PICKUPS):
                self.build(PickupRequest, i, spec, officer, collectors, citizens)

        self.report()

    # ------------------------------------------------------------------
    def ensure_users(self):
        call_command('seed_demo', stdout=StringIO())      # mc_officer, collector1, collector2, citizen1
        citizens = []
        for username, name in CITIZENS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'first_name': name, 'email': f'{username}@example.com'})
            if created:
                user.set_password(PASSWORD)
                user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            if not user.is_staff and profile.role != Profile.ROLE_CITIZEN:
                profile.role = Profile.ROLE_CITIZEN
            profile.city, profile.state = profile.city or CITY, profile.state or STATE
            profile.save()
            citizens.append(user)
        officer = User.objects.get(username='mc_officer')
        collectors = {1: User.objects.get(username='collector1'), 2: User.objects.get(username='collector2')}
        return officer, collectors, citizens

    # ------------------------------------------------------------------
    def build(self, model, i, spec, officer, collectors, citizens):
        is_complaint = model is Complaint
        now = timezone.now()
        base = now - timedelta(days=spec['d'], hours=spec.get('h', 0))
        collector = collectors.get(spec.get('col'))
        area = spec['area']

        fields = dict(user=citizens[spec['u']], area=area, address=spec['addr'],
                      city=CITY, state=STATE, pincode=PINCODES[area])
        if is_complaint:
            fields.update(category=spec['cat'], description=spec['desc'])
            verified, conf = spec['ai']
            reason = ('Garbage is clearly visible in the photo.' if verified
                      else 'No clear waste is visible in this photo.')
            fields.update(ai_verified=verified, ai_confidence=conf, ai_reason=reason)
        else:
            fields.update(waste_type=spec['wt'], notes=spec['notes'],
                          preferred_date=(base + timedelta(days=2)).date())
        obj = model(**fields)

        events = apply_workflow(obj, spec['status'], base, officer, collector,
                                note=spec.get('note', ''), reason=spec.get('reason', ''),
                                redo=spec.get('redo', ''))

        tag = 'c' if is_complaint else 'p'
        if is_complaint:                                    # "before" photo
            if self.samples:
                src = self.samples[i % len(self.samples)]
                content = src.read_bytes()
                ext = src.suffix.lower()
            else:
                content, ext = placeholder('before', spec['cat'].replace('_', ' ').title(), i), '.jpg'
            obj.image.save(f'seed_{tag}{i}{ext}', ContentFile(content), save=False)
        if obj.cleaned_at:                                  # "after" photo
            obj.after_image.save(f'seed_{tag}{i}_after.jpg',
                                 ContentFile(placeholder('after', 'Cleaned', 1000 + i)), save=False)
            obj.after_ai_score = spec.get('after', round(random.Random(i).uniform(3, 9), 1))
        obj.save()

        last = base
        for event, status, actor, note, when in events:
            log = ActivityLog.objects.create(kind=obj.kind, object_id=obj.pk, event=event,
                                             status=status, actor=actor, note=note)
            ActivityLog.objects.filter(pk=log.pk).update(created_at=when)
            last = max(last, when)
        # auto_now_add / auto_now ignore values on save(), so set the dates with update()
        update = {'created_at': base}
        if is_complaint:
            update['updated_at'] = last
        model.objects.filter(pk=obj.pk).update(**update)

    # ------------------------------------------------------------------
    def report(self):
        self.stdout.write(self.style.SUCCESS('Dummy data added.'))
        for label, model in (('Complaints', Complaint), ('Pickups', PickupRequest)):
            counts = Counter(model.objects.values_list('status', flat=True))
            detail = ', '.join(f'{k}: {v}' for k, v in sorted(counts.items()))
            self.stdout.write(f'  {label}: {model.objects.count()} ({detail})')
        self.stdout.write(f'Demo logins (password {PASSWORD}): mc_officer, collector1, collector2, '
                          + ', '.join(u for u, _ in CITIZENS))
