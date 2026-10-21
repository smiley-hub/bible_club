from django.shortcuts import render
from django.db.models import Prefetch

from events.models import Event, EventAlbum, EventPhoto
from .models import ClubProfile, FAQ, HistoryMilestone, HomeSlide, Organizer


def home(request):
    albums = EventAlbum.objects.public().select_related('event').prefetch_related(
        Prefetch('photos', queryset=EventPhoto.objects.filter(is_active=True))
    )[:2]
    return render(request, 'core/home.html', {
        'club': ClubProfile.objects.first(),
        'slides': HomeSlide.objects.filter(is_active=True),
        'next_event': Event.objects.upcoming().first() or Event.objects.undated().first(),
        'milestones': HistoryMilestone.objects.filter(is_published=True),
        'albums': albums,
        'faqs': FAQ.objects.filter(is_published=True),
    })


def our_story(request):
    return render(request, 'core/our_story.html', {
        'club': ClubProfile.objects.first(),
        'milestones': HistoryMilestone.objects.filter(is_published=True),
        'organizers': Organizer.objects.filter(is_active=True),
    })
