import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import Profile
from accounts.roles import available_collectors, get_role
from pickups.models import PickupRequest

from . import services
from .models import Complaint

TMP_MEDIA = tempfile.mkdtemp()
# smallest valid GIF
GIF = (b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff,\x00\x00\x00\x00'
       b'\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')


def make_user(username, role, approved=True, staff=False):
    user = User.objects.create_user(username, password='pass12345', is_staff=staff)
    profile = user.profile
    profile.role, profile.is_approved, profile.city = role, approved, 'Kanpur'
    profile.save()
    return user


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class WorkflowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.citizen = make_user('cit', Profile.ROLE_CITIZEN)
        self.officer = make_user('mc', Profile.ROLE_OFFICER, staff=True)
        self.collector = make_user('col', Profile.ROLE_COLLECTOR)
        self.other = make_user('col2', Profile.ROLE_COLLECTOR)
        self.complaint = Complaint.objects.create(
            user=self.citizen, category='garbage_on_road', description='x', area='Civil Lines',
            address='Near park', city='Kanpur', state='Uttar Pradesh', pincode='208001')

    def photo(self):
        return SimpleUploadedFile('after.gif', GIF, content_type='image/gif')

    def test_roles(self):
        self.assertEqual(get_role(self.citizen), 'citizen')
        self.assertEqual(get_role(self.officer), 'officer')
        self.assertEqual(get_role(self.collector), 'collector')

    def test_unapproved_collector_not_assignable(self):
        pending = make_user('newcol', Profile.ROLE_COLLECTOR, approved=False)
        self.assertNotIn(pending, available_collectors())
        with self.assertRaises(services.WorkflowError):
            services.approve(self.complaint, self.officer, pending)

    def test_reject_needs_reason(self):
        with self.assertRaises(services.WorkflowError):
            services.reject(self.complaint, self.officer, '   ')
        services.reject(self.complaint, self.officer, 'Address incomplete')
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'rejected')
        self.assertEqual(self.complaint.rejection_reason, 'Address incomplete')

    def test_full_happy_path(self):
        services.approve(self.complaint, self.officer)                 # no collector yet
        self.assertEqual(self.complaint.status, 'approved')
        services.accept(self.complaint, self.collector)                # collector claims it
        self.assertEqual(self.complaint.collector, self.collector)
        services.submit_cleaning(self.complaint, self.collector, self.photo(), 'done')
        self.assertEqual(self.complaint.status, 'cleaned')
        self.assertEqual(services.collector_stats(self.collector)['awaiting'], 1)
        services.verify_cleaning(self.complaint, self.officer)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'resolved')
        stats = services.collector_stats(self.collector)
        self.assertEqual((stats['cleaned'], stats['not_cleaned']), (1, 0))
        self.assertEqual(stats['rate'], 100)
        self.assertEqual(services.history(self.complaint).count(), 4)

    def test_send_back_and_redo(self):
        services.approve(self.complaint, self.officer, self.collector)
        services.submit_cleaning(self.complaint, self.collector, self.photo())
        with self.assertRaises(services.WorkflowError):
            services.send_back(self.complaint, self.officer, '')
        services.send_back(self.complaint, self.officer, 'Still some waste on the left')
        self.assertEqual(self.complaint.status, 'in_progress')
        self.assertEqual(services.collector_stats(self.collector)['redo'], 1)

    def test_other_collector_cannot_take_assigned_task(self):
        services.approve(self.complaint, self.officer, self.collector)
        with self.assertRaises(services.WorkflowError):
            services.accept(self.complaint, self.other)

    def test_pickup_uses_same_workflow(self):
        pickup = PickupRequest.objects.create(
            user=self.citizen, waste_type='wet', address='12 Gandhi Road', area='Civil Lines',
            city='Kanpur', state='Uttar Pradesh', pincode='208001', preferred_date='2030-01-01')
        services.approve(pickup, self.officer, self.collector)
        services.submit_cleaning(pickup, self.collector, self.photo())
        services.verify_cleaning(pickup, self.officer)
        self.assertEqual(services.collector_stats(self.collector)['cleaned'], 1)

    def test_citizen_cancel_only_when_pending(self):
        services.approve(self.complaint, self.officer)
        with self.assertRaises(services.WorkflowError):
            services.cancel_by_owner(self.complaint, self.citizen)

    def test_google_maps_links(self):
        url = self.complaint.maps_directions_url
        self.assertTrue(url.startswith('https://www.google.com/maps/dir/?api=1'))
        self.assertIn('208001', url)
        self.assertIn('Kanpur', url)
