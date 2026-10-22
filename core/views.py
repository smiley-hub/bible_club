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


def contact(request):
    from smtplib import SMTPException
    from time import time
    from django.conf import settings
    from django.contrib import messages
    from django.core.mail import EmailMessage
    from django.shortcuts import redirect
    from .forms import ContactForm

    club = ClubProfile.objects.first()
    delivery = bool(settings.CONTACT_FORM_ENABLED and club and club.contact_email)
    # Console/dummy/file backends must never be presented as real delivery.
    delivery = delivery and settings.EMAIL_BACKEND not in {
        'django.core.mail.backends.console.EmailBackend',
        'django.core.mail.backends.dummy.EmailBackend',
        'django.core.mail.backends.filebased.EmailBackend',
    }
    available = delivery or settings.DEBUG
    form = ContactForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        if not available:
            form.add_error(None, 'The message form is unavailable. Please use the contact links on this page.')
        elif form.is_valid():
            if not delivery:
                messages.info(request, 'Preview complete. Your message has not been sent. Please use the club contact links to get in touch.')
                return redirect('core:contact')
            elif time() - request.session.get('contact_last_sent', 0) < 60:
                form.add_error(None, 'Please wait a minute before sending another message.')
            else:
                data = form.cleaned_data
                topic = dict(form.fields['topic'].choices)[data['topic']]
                email = EmailMessage(
                    subject=f'Club website: {topic}',
                    body=f"Name: {data['name']}\nEmail: {data['email']}\nTopic: {topic}\n\n{data['message']}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[club.contact_email], reply_to=[data['email']],
                )
                try:
                    sent = email.send(fail_silently=False)
                except (SMTPException, OSError, ValueError):
                    sent = 0
                if sent:
                    request.session['contact_last_sent'] = time()
                    messages.success(request, 'Your message has been sent. Thank you for getting in touch.')
                    return redirect('core:contact')
                form.add_error(None, 'Your message could not be sent. Please try again later or use the contact links below.')
    return render(request, 'core/contact.html', {
        'club': club, 'form': form, 'form_available': available,
        'preview_mode': available and not delivery,
        'contact_photo': HomeSlide.objects.filter(is_active=True).first(),
        'faqs': FAQ.objects.filter(is_published=True),
    })
