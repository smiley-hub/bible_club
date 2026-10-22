from datetime import timedelta
from io import StringIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.tests import photo_file
from .models import Event, EventAlbum, EventPhoto


class PublicationTests(TestCase):
    def test_only_published_future_events_are_upcoming(self):
        future = timezone.now() + timedelta(days=2)
        past = timezone.now() - timedelta(days=2)
        published = Event.objects.create(title='Next', slug='next', status='published', starts_at=future)
        draft = Event.objects.create(title='Draft', slug='draft', starts_at=future)
        cancelled = Event.objects.create(title='Cancelled', slug='cancelled', status='cancelled', starts_at=future)
        Event.objects.create(title='Past', slug='past', status='published', starts_at=past)
        undated = Event.objects.create(title='Undated', slug='undated', status='published')
        self.assertEqual(list(Event.objects.upcoming()), [published])
        self.assertEqual(list(Event.objects.undated()), [undated])
        self.assertNotIn(draft, Event.objects.public())
        self.assertIn(cancelled, Event.objects.public())

    def test_album_requires_past_published_event_and_own_publication(self):
        event = Event.objects.create(title='Gathering', slug='gathering', starts_at=timezone.now() - timedelta(days=1))
        album = EventAlbum.objects.create(event=event, title='Memories', is_published=True)
        self.assertFalse(EventAlbum.objects.public().exists())
        event.status = 'published'
        event.save()
        self.assertEqual(list(EventAlbum.objects.public()), [album])
        album.is_published = False
        album.save()
        self.assertFalse(EventAlbum.objects.public().exists())
        album.is_published = True
        album.save()
        event.starts_at = timezone.now() + timedelta(days=1)
        event.save()
        self.assertFalse(EventAlbum.objects.public().exists())

    def test_invalid_end_time(self):
        now = timezone.now()
        for start, end in [(None, now), (now, now), (now, now - timedelta(hours=1))]:
            with self.subTest(start=start), self.assertRaises(ValidationError):
                Event(title='Invalid', slug='invalid', starts_at=start, ends_at=end).full_clean()


class EventAdminTests(TestCase):
    def setUp(self):
        call_command('setup_leaders', stdout=StringIO())
        user = User.objects.create_user('leader', is_staff=True)
        user.groups.add(Group.objects.get(name='Club leaders'))
        self.client.force_login(user)

    def test_leader_can_create_event_and_change_date(self):
        data = {'title': 'Bible study', 'slug': 'bible-study', 'description': 'Read together',
                'category': 'bible-study', 'status': 'draft', '_save': 'Save'}
        response = self.client.post(reverse('admin:events_event_add'), data)
        self.assertEqual(response.status_code, 302)
        event = Event.objects.get()
        data.update({'starts_at_0': '2027-05-10', 'starts_at_1': '18:00:00', 'status': 'published'})
        response = self.client.post(reverse('admin:events_event_change', args=[event.pk]), data)
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.starts_at.date().isoformat(), '2027-05-10')
        self.assertEqual(event.status, 'published')

    def test_leader_can_upload_album_photo_inline(self):
        event = Event.objects.create(title='Picnic', slug='picnic')
        with TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            response = self.client.post(reverse('admin:events_eventalbum_add'), {
                'event': event.pk, 'title': 'Picnic album',
                'photos-TOTAL_FORMS': '1', 'photos-INITIAL_FORMS': '0',
                'photos-MIN_NUM_FORMS': '0', 'photos-MAX_NUM_FORMS': '1000',
                'photos-0-image': photo_file(), 'photos-0-alt_text': 'Friends at a picnic',
                'photos-0-display_order': '0', 'photos-0-is_active': 'on', '_save': 'Save',
            })
            self.assertEqual(response.status_code, 302)
            photo = EventPhoto.objects.get()
            self.assertEqual(photo.album.event, event)
            self.assertTrue(photo.image.storage.exists(photo.image.name))

class EventPageTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.future = Event.objects.create(title='Future gathering', slug='future', status='published', starts_at=now + timedelta(days=2))
        self.draft = Event.objects.create(title='Private draft', slug='draft', starts_at=now + timedelta(days=1))
        self.past = Event.objects.create(title='Past gathering', slug='past', status='published', starts_at=now - timedelta(days=2), category='outdoors')
        self.album = EventAlbum.objects.create(event=self.past, title='Outdoor memories', is_published=True)

    def test_list_filters_and_publication(self):
        response = self.client.get(reverse('events:list'))
        self.assertContains(response, 'Future gathering')
        self.assertContains(response, 'Outdoor memories')
        self.assertNotContains(response, 'Private draft')
        response = self.client.get(reverse('events:list'), {'category': 'bible-study'})
        self.assertNotContains(response, 'Outdoor memories')
        self.assertContains(response, 'Future gathering')
        response = self.client.get(reverse('events:list'), {'category': 'invalid', 'page': 'invalid'})
        self.assertContains(response, 'Outdoor memories')

    def test_details_drafts_cancellations_and_undated_events(self):
        self.assertEqual(self.client.get(reverse('events:detail', args=['draft'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('events:detail', args=['missing'])).status_code, 404)
        self.future.status = 'cancelled'
        self.future.save()
        self.assertContains(self.client.get(reverse('events:detail', args=['future'])), 'This event has been cancelled.')
        self.assertContains(self.client.get(reverse('events:list')), 'Cancelled')
        self.future.starts_at = None
        self.future.status = 'published'
        self.future.save()
        self.assertContains(self.client.get(reverse('events:detail', args=['future'])), 'To be confirmed')

    def test_album_only_exposes_active_photos_and_published_past_events(self):
        EventPhoto.objects.create(album=self.album, image='demo/visible.jpg', alt_text='Visible photo', is_active=True)
        EventPhoto.objects.create(album=self.album, image='demo/private.jpg', alt_text='Private photo')
        url = reverse('events:album', args=['past'])
        response = self.client.get(url)
        self.assertContains(response, 'Visible photo')
        self.assertNotContains(response, 'Private photo')
        self.album.is_published = False
        self.album.save()
        self.assertEqual(self.client.get(url).status_code, 404)
        self.album.is_published = True
        self.album.save()
        self.past.starts_at = timezone.now() + timedelta(days=3)
        self.past.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_ongoing_events_and_pagination(self):
        ongoing = Event.objects.create(title='Happening now', slug='ongoing', status='published', starts_at=timezone.now()-timedelta(hours=1), ends_at=timezone.now()+timedelta(hours=1))
        for i in range(9):
            Event.objects.create(title=f'Upcoming {i}', slug=f'upcoming-{i}', status='published', starts_at=timezone.now()+timedelta(days=i+4))
        response = self.client.get(reverse('events:list'))
        self.assertContains(response, ongoing.title)
        self.assertEqual(len(response.context['gatherings']), 7)
        response = self.client.get(reverse('events:list'), {'gatherings': 2})
        self.assertEqual(len(response.context['gatherings']), 4)
        self.assertContains(response, 'Upcoming 8')

    def test_empty_states_and_escaped_content(self):
        self.future.description = '<script>alert(1)</script>'
        self.future.save()
        response = self.client.get(reverse('events:detail', args=['future']))
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        Event.objects.all().delete()
        response = self.client.get(reverse('events:list'))
        self.assertContains(response, 'Good things are ahead.')
        self.assertContains(response, 'There are memories to be made.')
