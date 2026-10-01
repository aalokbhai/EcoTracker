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


# --------------------------------------------------------------------------- AI photo check (Gemini)
import io as _io
import json as _json
import os as _os
import tempfile as _tempfile
import urllib.error as _urlerror
from unittest import mock as _mock

from django.test import SimpleTestCase as _SimpleTestCase
from PIL import Image as _Image

from complaints import ai as _ai


class _FakeResponse:
    def __init__(self, body):
        self._body = _json.dumps(body).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _gemini_reply(waste_present, confidence, reason='Some reason.'):
    answer = _json.dumps({'waste_present': waste_present, 'confidence': confidence, 'reason': reason})
    return {'candidates': [{'content': {'parts': [{'text': answer}]}}]}


class GeminiCheckTests(_SimpleTestCase):
    def setUp(self):
        fd, self.path = _tempfile.mkstemp(suffix='.jpg')
        _os.close(fd)
        _Image.new('RGB', (1600, 1200), (90, 80, 70)).save(self.path, 'JPEG')
        self.addCleanup(_os.remove, self.path)
        patcher = _mock.patch.dict(_os.environ, {'GEMINI_API_KEY': 'test-key'})
        patcher.start()
        self.addCleanup(patcher.stop)
        sleeper = _mock.patch('complaints.ai.time.sleep')
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def test_waste_is_verified_with_confidence(self):
        with _mock.patch('complaints.ai.urllib.request.urlopen', return_value=_FakeResponse(_gemini_reply(True, 92, 'A pile of garbage.'))):
            result = _ai.analyze_image(self.path)
        self.assertTrue(result.verified)
        self.assertEqual(result.percent, 92.0)
        self.assertEqual(result.reason, 'A pile of garbage.')

    def test_no_waste_is_flagged_and_confidence_is_inverted(self):
        with _mock.patch('complaints.ai.urllib.request.urlopen', return_value=_FakeResponse(_gemini_reply(False, 90))):
            verified, percent = _ai.verify_image(self.path)
        self.assertFalse(verified)
        self.assertEqual(percent, 10.0)

    def test_missing_key_skips_the_check(self):
        with _mock.patch.dict(_os.environ, {'GEMINI_API_KEY': ''}):
            self.assertEqual(_ai.verify_image(self.path), (None, None))

    def test_switch_off(self):
        with _mock.patch.dict(_os.environ, {'AI_CHECK': 'off'}):
            self.assertEqual(_ai.verify_image(self.path), (None, None))

    def test_network_error_does_not_break_the_complaint(self):
        with _mock.patch('complaints.ai.urllib.request.urlopen', side_effect=_urlerror.URLError('offline')):
            self.assertEqual(_ai.verify_image(self.path), (None, None))

    def test_garbage_reply_is_handled(self):
        bad = {'candidates': [{'content': {'parts': [{'text': 'not json'}]}}]}
        with _mock.patch('complaints.ai.urllib.request.urlopen', return_value=_FakeResponse(bad)):
            self.assertEqual(_ai.verify_image(self.path), (None, None))

    def test_retries_without_schema_when_gemini_returns_400(self):
        err = _urlerror.HTTPError('u', 400, 'Bad', {}, _io.BytesIO(b'{"error": "schema"}'))
        with _mock.patch('complaints.ai.urllib.request.urlopen',
                         side_effect=[err, _FakeResponse(_gemini_reply(True, 80))]) as call:
            result = _ai.analyze_image(self.path)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(result.percent, 80.0)

    def test_sends_key_in_header_and_small_jpeg(self):
        with _mock.patch('complaints.ai.urllib.request.urlopen', return_value=_FakeResponse(_gemini_reply(True, 70))) as call:
            _ai.analyze_image(self.path)
        request = call.call_args[0][0]
        self.assertEqual(request.get_header('X-goog-api-key'), 'test-key')
        self.assertNotIn('test-key', request.full_url)
        body = _json.loads(request.data)
        self.assertEqual(body['contents'][0]['parts'][1]['inline_data']['mime_type'], 'image/jpeg')

    def test_hindi_prompt_when_site_is_in_hindi(self):
        self.assertIn('Hindi', _ai._prompt('hi'))
        self.assertNotIn('Hindi', _ai._prompt('en'))


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class ReportWithAITests(TestCase):
    """The whole path: citizen uploads a photo -> AI result is stored -> shown on the detail page."""

    def setUp(self):
        self.citizen = make_user('cit_ai', Profile.ROLE_CITIZEN)
        self.client.force_login(self.citizen)

    def post_complaint(self):
        from django.urls import reverse
        photo = SimpleUploadedFile('waste.gif', GIF, content_type='image/gif')
        return self.client.post(reverse('report_complaint'), {
            'category': 'garbage_on_road', 'area': 'Civil Lines', 'address': 'Near the park',
            'city': 'Kanpur', 'state': 'Uttar Pradesh', 'pincode': '208001',
            'description': 'Garbage pile on the road', 'image': photo}, follow=True)

    def test_ai_result_is_saved_and_shown(self):
        result = _ai.AIResult(True, 93.4, 'A large pile of garbage on the roadside.')
        with _mock.patch('complaints.views.analyze_image', return_value=result):
            response = self.post_complaint()
        complaint = Complaint.objects.get(user=self.citizen)
        self.assertTrue(complaint.ai_verified)
        self.assertEqual(complaint.ai_confidence, 93.4)
        self.assertEqual(complaint.ai_reason, 'A large pile of garbage on the roadside.')
        self.assertContains(response, '93.4%')
        self.assertContains(response, 'A large pile of garbage on the roadside.')

    def test_flagged_when_ai_says_no_waste(self):
        with _mock.patch('complaints.views.analyze_image', return_value=_ai.AIResult(False, 12.0, 'Only a clean road.')):
            response = self.post_complaint()
        self.assertIs(Complaint.objects.get(user=self.citizen).ai_verified, False)
        self.assertContains(response, 'flagged for manual review')

    def test_complaint_is_saved_even_when_ai_is_unavailable(self):
        with _mock.patch('complaints.views.analyze_image', return_value=None):
            self.post_complaint()
        complaint = Complaint.objects.get(user=self.citizen)
        self.assertIsNone(complaint.ai_verified)
        self.assertIsNone(complaint.ai_confidence)
