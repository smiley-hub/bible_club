from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from core.models import ClubProfile
from .models import Event, EventAlbum


def event_list(request):
    now = timezone.now()
    gatherings = Event.objects.public().filter(
        Q(starts_at__gte=now) | Q(starts_at__isnull=True) | Q(ends_at__gte=now)
    ).order_by(F('starts_at').asc(nulls_last=True), 'pk')
    albums = EventAlbum.objects.public().select_related('event')
    category = request.GET.get('category', '')
    if category not in dict(Event.Category.choices):
        category = ''
    if category:
        albums = albums.filter(event__category=category)
    return render(request, 'events/list.html', {
        'club': ClubProfile.objects.first(),
        'gatherings': Paginator(gatherings, 7).get_page(request.GET.get('gatherings')),
        'albums': Paginator(albums, 6).get_page(request.GET.get('page')),
        'categories': Event.Category.choices, 'category': category,
    })


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.public(), slug=slug)
    return render(request, 'events/detail.html', {
        'club': ClubProfile.objects.first(), 'event': event,
        'is_past': bool(event.starts_at and (event.ends_at or event.starts_at) < timezone.now()),
        'album': EventAlbum.objects.public().filter(event=event).first(),
    })


def album_detail(request, slug):
    album = get_object_or_404(EventAlbum.objects.public().select_related('event'), event__slug=slug)
    return render(request, 'events/album.html', {
        'club': ClubProfile.objects.first(), 'album': album,
        'photos': Paginator(album.photos.filter(is_active=True), 24).get_page(request.GET.get('page')),
    })
