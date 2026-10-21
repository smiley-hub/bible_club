from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.request import urlopen

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import ClubProfile, FAQ, HistoryMilestone, HomeSlide, Organizer
from core.validators import validate_photo
from events.models import Event, EventAlbum, EventPhoto


PHOTOS = [
    ('study', '1522202176988-66273c2fd55f', 'Stock photo: three people talking around laptops at a table'),
    ('community', '1523240795612-9a054b0db644', 'Stock photo: people working together beside library shelves'),
    ('together', '1511988617509-a57c8a288659', 'Stock photo: friends laughing together outdoors'),
]


class Command(BaseCommand):
    help = 'Add labeled demo content without overwriting existing matching records.'

    def add_arguments(self, parser):
        parser.add_argument('--download-images', action='store_true', help='Download missing stock photos from Unsplash.')

    def handle(self, *args, **options):
        directory = Path(settings.MEDIA_ROOT) / 'demo'
        directory.mkdir(parents=True, exist_ok=True)
        for name, source, _ in PHOTOS:
            path = directory / f'{name}.jpg'
            if not path.exists():
                if not options['download_images']:
                    raise CommandError(f'Missing {path}. Use --download-images to obtain the demo photos.')
                url = f'https://images.unsplash.com/photo-{source}?auto=format&fit=max&w=1600&q=85'
                try:
                    with urlopen(url, timeout=30) as response:
                        data = response.read(10 * 1024 * 1024 + 1)
                    from django.core.files.base import ContentFile
                    validate_photo(ContentFile(data, name=path.name))
                    path.write_bytes(data)
                except Exception as exc:
                    raise CommandError(f'Could not download {name}: {exc}') from exc
            with path.open('rb') as source_file:
                validate_photo(File(source_file))

        created = 0

        def add(model, lookup, **defaults):
            nonlocal created
            obj, new = model.objects.get_or_create(**lookup, defaults=defaults)
            created += int(new)
            return obj

        today = timezone.localdate()
        at_six = timezone.make_aware(datetime.combine(today, time(18)))
        with transaction.atomic():
            if not ClubProfile.objects.exists():
                add(ClubProfile, {'singleton': 1},
                    name='METU Bible Club',
                    welcome_text='Explore the Bible, ask honest questions, and build friendships. There is room for you in the conversation.',
                    purpose='Demo introduction: a community shaped by faith, friendship, and honest conversations. Replace this with your club’s own story.',
                    meeting_information='Demo preview — dates, venues, milestones, and photos are sample content, not confirmed club information.',
                    contact_email='hello@example.com')

            for index, (name, _, alt) in enumerate(PHOTOS):
                add(HomeSlide, {'title': f'[Demo] {name.title()}'}, image=f'demo/{name}.jpg',
                    alt_text=alt, caption='Demo stock photo — not METU Bible Club members',
                    display_order=index, is_active=True)

            for index, (title, story) in enumerate([
                ('The first conversation', 'Sample milestone: this is where you could tell the story of the first meeting and the people who started it.'),
                ('Growing together', 'Sample milestone: describe how friendships grew and new students became part of the community.'),
                ('The next chapter', 'Sample milestone: share what the community is doing today and what you hope comes next.'),
            ]):
                add(HistoryMilestone, {'title': f'[Demo] {title}'}, year=today.year - 2 + index,
                    story=story + ' The year shown is illustrative, not a historical claim.',
                    display_order=index, is_published=True)

            for index, (question, answer) in enumerate([
                ('Can I come if I am just curious?', 'Sample answer: yes, bring your questions and join the conversation. Leaders should confirm this wording before launch.'),
                ('What should I bring?', 'Sample answer: a Bible or Bible app and a notebook can be useful. Replace this with the club’s actual guidance.'),
                ('Where do you meet?', 'Sample answer: check the next-gathering panel for the date and room. Demo dates and rooms are placeholders.'),
            ]):
                add(FAQ, {'question': f'[Demo] {question}'}, answer=answer, display_order=index, is_published=True)

            for index, role in enumerate(['Club coordinator', 'Events organizer']):
                add(Organizer, {'name': f'[Demo] Organizer {index + 1}'}, role=role, display_order=index, is_active=True)

            for index, (title, days, category) in enumerate([
                ('Bible study & conversation', 3, 'bible-study'),
                ('Community afternoon', 10, 'community'),
                ('An afternoon together', -7, 'outdoors'),
                ('Around the table', -21, 'community'),
            ]):
                image_name, _, alt = PHOTOS[index % len(PHOTOS)]
                start = at_six + timedelta(days=days)
                event = add(Event, {'slug': f'demo-{index + 1}'}, title=f'[Demo] {title}',
                    description='A sample gathering for previewing the website. This is not a scheduled club event. Replace the title, date, venue, and description with confirmed details.',
                    starts_at=start, ends_at=start + timedelta(hours=1), venue='Demo venue — room to be confirmed',
                    category=category, status='published', image=f'demo/{image_name}.jpg', alt_text=alt)
                if days < 0:
                    album = add(EventAlbum, {'event': event}, title=f'[Demo] {title}',
                        recap='Sample album using stock photography. Replace these with your own memories and event recap.',
                        is_published=True)
                    for order, (name, _, photo_alt) in enumerate(PHOTOS):
                        add(EventPhoto, {'album': album, 'image': f'demo/{name}.jpg'},
                            alt_text=photo_alt, caption='Demo stock photo — not a club event', display_order=order, is_active=True)

        self.stdout.write(self.style.SUCCESS(f'Added {created} demo records. Existing matching content was preserved.'))
