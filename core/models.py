from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .validators import validate_photo


class OrderedContent(models.Model):
    display_order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first.')

    class Meta:
        abstract = True
        ordering = ['display_order', 'pk']


class PhotoContent(models.Model):
    image = models.ImageField(upload_to='club/', blank=True, validators=[validate_photo])
    alt_text = models.CharField(max_length=250, blank=True, help_text='Describe the photo for someone who cannot see it.')

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.image and not self.alt_text.strip():
            raise ValidationError({'alt_text': 'Add a description for this photo.'})


class ClubProfile(models.Model):
    singleton = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    name = models.CharField(max_length=150, default='METU Bible Club')
    welcome_text = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    beliefs = models.TextField(blank=True)
    meeting_information = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    social_url = models.URLField(blank=True)

    class Meta:
        verbose_name = 'club profile'
        constraints = [models.CheckConstraint(condition=models.Q(singleton=1), name='one_club_profile')]

    def __str__(self):
        return self.name


class HomeSlide(OrderedContent, PhotoContent):
    title = models.CharField(max_length=150, help_text='Internal label to help identify this slide.')
    image = models.ImageField(upload_to='homepage/%Y/%m/', validators=[validate_photo])
    caption = models.CharField(max_length=250, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class HistoryMilestone(OrderedContent, PhotoContent):
    title = models.CharField(max_length=150)
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    story = models.TextField()
    image = models.ImageField(upload_to='history/%Y/%m/', blank=True, validators=[validate_photo])
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.year}: {self.title}'


class Organizer(OrderedContent, PhotoContent):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    image = models.ImageField(upload_to='organizers/%Y/%m/', blank=True, validators=[validate_photo])
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class FAQ(OrderedContent):
    question = models.CharField(max_length=250)
    answer = models.TextField()
    is_published = models.BooleanField(default=False)

    class Meta(OrderedContent.Meta):
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
