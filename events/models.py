from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import OrderedContent, PhotoContent
from core.validators import validate_photo


class EventQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status__in=['published', 'cancelled'])

    def upcoming(self):
        return self.filter(status='published', starts_at__gte=timezone.now()).order_by('starts_at', 'pk')

    def undated(self):
        return self.filter(status='published', starts_at__isnull=True).order_by('title', 'pk')


class Event(PhotoContent):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CANCELLED = 'cancelled', 'Cancelled'

    class Category(models.TextChoices):
        BIBLE_STUDY = 'bible-study', 'Bible study'
        COMMUNITY = 'community', 'Community'
        OUTDOORS = 'outdoors', 'Outdoors'
        OTHER = 'other', 'Other'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, help_text='URL name. Keep this unchanged after sharing the event link.')
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=250, blank=True)
    directions_url = models.URLField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.COMMUNITY)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    image = models.ImageField('cover image', upload_to='events/covers/%Y/%m/', blank=True, validators=[validate_photo])
    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ['-starts_at', 'title']
        constraints = [models.CheckConstraint(
            condition=models.Q(ends_at__isnull=True) | (
                models.Q(starts_at__isnull=False) & models.Q(ends_at__gt=models.F('starts_at'))
            ), name='event_end_after_start',
        )]

    def clean(self):
        super().clean()
        if self.ends_at and (not self.starts_at or self.ends_at <= self.starts_at):
            raise ValidationError({'ends_at': 'Set a start time and an end time later than the start.'})

    def __str__(self):
        return self.title


class AlbumQuerySet(models.QuerySet):
    def public(self):
        return self.filter(
            is_published=True, event__status=Event.Status.PUBLISHED,
            event__starts_at__lt=timezone.now(),
        ).order_by('-event__starts_at', '-pk')


class EventAlbum(PhotoContent):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='album')
    title = models.CharField(max_length=200)
    recap = models.TextField(blank=True)
    image = models.ImageField('album cover', upload_to='events/albums/%Y/%m/', blank=True, validators=[validate_photo])
    is_published = models.BooleanField(default=False, help_text='Appears publicly only for a past, published event.')
    objects = AlbumQuerySet.as_manager()

    @property
    def cover_image(self):
        return self.image or self.event.image

    @property
    def cover_alt_text(self):
        return self.alt_text if self.image else self.event.alt_text

    def __str__(self):
        return self.title


class EventPhoto(OrderedContent, PhotoContent):
    album = models.ForeignKey(EventAlbum, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='events/photos/%Y/%m/', validators=[validate_photo])
    caption = models.CharField(max_length=250, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.caption or self.alt_text or f'Photo {self.pk or "(new)"}'
