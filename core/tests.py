from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import ClubProfile, HomeSlide
from .validators import validate_photo


def photo_file(name='photo.png'):
    content = BytesIO()
    Image.new('RGB', (12, 12), 'green').save(content, format='PNG')
    return SimpleUploadedFile(name, content.getvalue(), content_type='image/png')


class LeaderAdminTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        call_command('setup_leaders', stdout=StringIO())
        self.leader = User.objects.create_user('leader', is_staff=True)
        self.leader.groups.add(Group.objects.get(name='Club leaders'))
        self.client.force_login(self.leader)

    def test_leader_can_upload_replace_hide_and_remove_slide(self):
        url = reverse('admin:core_homeslide_add')
        response = self.client.post(url, {
            'title': 'Welcome', 'image': photo_file(), 'alt_text': 'Students at a table',
            'display_order': 2, 'is_active': 'on', '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        slide = HomeSlide.objects.get()
        original_name = slide.image.name
        self.assertTrue(slide.image.storage.exists(original_name))
        response = self.client.post(reverse('admin:core_homeslide_change', args=[slide.pk]), {
            'title': 'Updated', 'image': photo_file('replacement.png'),
            'alt_text': 'Friends outside', 'display_order': 1, '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        slide.refresh_from_db()
        self.assertFalse(slide.is_active)
        self.assertEqual(slide.display_order, 1)
        self.assertNotEqual(slide.image.name, original_name)
        response = self.client.post(reverse('admin:core_homeslide_delete', args=[slide.pk]), {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(HomeSlide.objects.exists())

    def test_upload_requires_accessibility_description(self):
        response = self.client.post(reverse('admin:core_homeslide_add'), {
            'title': 'Welcome', 'image': photo_file(), 'display_order': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('alt_text', response.context['adminform'].form.errors)
        self.assertFalse(HomeSlide.objects.exists())

    def test_permissions_and_anonymous_login(self):
        self.assertEqual(self.client.get(reverse('admin:auth_user_changelist')).status_code, 403)
        unprivileged = User.objects.create_user('staff-only', is_staff=True)
        self.client.force_login(unprivileged)
        self.assertEqual(self.client.get(reverse('admin:core_homeslide_add')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('admin:core_homeslide_add')).status_code, 302)

    def test_all_content_admin_forms_render(self):
        for app, model in [('core', 'clubprofile'), ('core', 'homeslide'),
                           ('core', 'historymilestone'), ('core', 'organizer'),
                           ('core', 'faq'), ('events', 'event'), ('events', 'eventalbum')]:
            with self.subTest(model=model):
                self.assertEqual(self.client.get(reverse(f'admin:{app}_{model}_add')).status_code, 200)

    def test_single_club_profile(self):
        ClubProfile.objects.create()
        self.assertEqual(self.client.get(reverse('admin:core_clubprofile_add')).status_code, 403)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClubProfile.objects.create()


class PhotoValidationTests(TestCase):
    def test_rejects_disguised_non_image(self):
        with self.assertRaises(ValidationError):
            validate_photo(SimpleUploadedFile('fake.png', b'not an image'))

    def test_rejects_oversized_file(self):
        image = photo_file()
        image.size = 11 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_photo(image)

    def test_accepts_valid_image_and_rewinds(self):
        image = photo_file()
        validate_photo(image)
        self.assertEqual(image.tell(), 0)
