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


class StoryPageTests(TestCase):
    def test_empty_story_and_navigation(self):
        response = self.client.get(reverse('core:our_story'))
        self.assertContains(response, 'Every chapter brought us here.')
        self.assertContains(response, 'Our story is still unfolding.')
        self.assertNotContains(response, 'data-journey aria-label')
        self.assertContains(response, 'href="/#gatherings"')
        self.assertContains(response, 'aria-current="page">Our Story')

    def test_published_milestones_and_active_organizers_only(self):
        from .models import HistoryMilestone, Organizer
        HistoryMilestone.objects.create(title='Hidden chapter', year=2020, story='Not public')
        HistoryMilestone.objects.create(title='Later chapter', year=2024, story='Later story', is_published=True, display_order=2)
        HistoryMilestone.objects.create(title='First chapter', year=2022, story='First story', is_published=True, display_order=1)
        Organizer.objects.create(name='Private organizer', role='Leader')
        Organizer.objects.create(name='Public organizer', role='Coordinator', is_active=True)
        response = self.client.get(reverse('core:our_story'))
        self.assertContains(response, 'First story')
        self.assertContains(response, 'Later story')
        self.assertContains(response, 'Public organizer')
        self.assertNotContains(response, 'Hidden chapter')
        self.assertNotContains(response, 'Private organizer')
        self.assertLess(response.content.index(b'First chapter'), response.content.index(b'Later chapter'))

    def test_profile_content_is_present_and_escaped(self):
        ClubProfile.objects.create(purpose='Our shared purpose', beliefs='<script>unsafe()</script>')
        response = self.client.get(reverse('core:our_story'))
        self.assertContains(response, 'Our shared purpose')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>unsafe()</script>')


class HomepageTests(TestCase):
    def test_empty_site_has_welcome_fonts_and_no_fake_photos(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'A place to belong.')
        self.assertContains(response, 'fonts/lora.ttf')
        self.assertContains(response, 'fonts/source-sans-3.ttf')
        self.assertContains(response, 'Community photos coming soon')
        self.assertNotContains(response, 'data-slideshow')

    def test_public_content_only_and_slide_order(self):
        from .models import FAQ, HistoryMilestone
        HomeSlide.objects.create(title='Hidden', image='hidden.png', alt_text='Hidden photo')
        HomeSlide.objects.create(title='Second', image='second.png', alt_text='Second photo', is_active=True, display_order=2)
        HomeSlide.objects.create(title='First', image='first.png', alt_text='First photo', is_active=True, display_order=1)
        FAQ.objects.create(question='Private question', answer='Private answer')
        FAQ.objects.create(question='Public question', answer='Public answer', is_published=True)
        HistoryMilestone.objects.create(title='Private history', year=2020, story='Private story')
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'data-slideshow')
        self.assertNotContains(response, 'Hidden photo')
        self.assertNotContains(response, 'Private question')
        self.assertNotContains(response, 'Private history')
        self.assertContains(response, 'Public answer')
        self.assertLess(response.content.index(b'First photo'), response.content.index(b'Second photo'))

    def test_next_event_and_album_photos_obey_publication_rules(self):
        from datetime import timedelta
        from django.utils import timezone
        from events.models import Event, EventAlbum, EventPhoto
        now = timezone.now()
        Event.objects.create(title='Draft event', slug='draft', starts_at=now + timedelta(days=1))
        Event.objects.create(title='Public event', slug='public', status='published', starts_at=now + timedelta(days=2))
        past = Event.objects.create(title='Past event', slug='past', status='published', starts_at=now - timedelta(days=2))
        album = EventAlbum.objects.create(event=past, title='Our memories', is_published=True)
        EventPhoto.objects.create(album=album, image='hidden.png', alt_text='Hidden album photo')
        EventPhoto.objects.create(album=album, image='public.png', alt_text='Public album photo', is_active=True)
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Public event')
        self.assertNotContains(response, 'Draft event')
        self.assertContains(response, 'Our memories')
        self.assertContains(response, 'Public album photo')
        self.assertNotContains(response, 'Hidden album photo')

    def test_club_content_is_escaped_and_contact_works(self):
        ClubProfile.objects.create(name='Our Club', welcome_text='<script>alert(1)</script>', contact_email='club@example.com')
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Our Club')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, 'mailto:club@example.com')
