# Leader editing guide

## First login

Start the development server and open `http://127.0.0.1:8000/admin/`.
If no administrator exists, create one in a terminal:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Choose your own password. No default credentials are created by the project.

## Give a leader access

Run `python manage.py setup_leaders` using the project environment after migrating.
An administrator can then create a user in Django admin, enable **Staff status**,
and assign the **Club leaders** group. Leave **Superuser status** off for ordinary
leaders. The group can manage club content but cannot manage accounts or permissions.
The setup command can be rerun; it refreshes this group's content permissions.

## Content sections

- **Club profiles:** create the single profile, then edit welcome text, purpose,
  beliefs, meeting information, email, and social link there.
- **Home slides:** upload a photo and enter an internal title and alt text. Lower
  display-order numbers come first. Enable Active when ready. Change the upload
  to replace the image, uncheck Active to hide it, or delete the slide record.
- **History milestones:** enter year, title, story, optional image, and order;
  enable Published when ready.
- **Organizers:** manage names, roles, optional portraits, order, and visibility.
- **FAQs:** manage questions, answers, order, and publication.
- **Events:** create a title, URL slug, description, category, dates, location,
  and optional cover photo. Save as Draft until ready, then choose Published.
  Choose Cancelled when a published gathering is cancelled. Keep shared URL slugs
  unchanged. Dates may be blank while awaiting confirmation; an end time requires
  an earlier start time. Times use the configured `DJANGO_TIME_ZONE`.
- **Event albums:** choose the event and enter an album title and recap. Upload
  individual photos using the rows beneath the album form; add rows as needed.
  Set each photo's alt text, caption, order, and Active flag. Album publication is
  separate from event publication; only past published events qualify for public
  album listings. An omitted album cover falls back to the event's cover photo.

## Photos

Accepted formats: JPEG, PNG, WebP. Maximum file size: 10 MB. Maximum resolution:
24 megapixels. Every uploaded photo requires a description for accessibility.
Photo previews appear when editing a saved item. Files are stored under `media/`.
This milestone validates uploads but does not yet generate resized thumbnails.

Replacing or deleting a record leaves the old physical file in storage; it is no
longer referenced by that record. Hiding a record also does not revoke a previously
shared direct media URL. File cleanup and any stricter private-media requirements
must be handled separately. Back up the database and media folder together.

## Current milestone

The admin editing workflow and public homepage work. Active homepage slides
appear in display order; with two or more, visitors get arrows, position controls,
and autoplay with a pause button. Reduced-motion preferences disable autoplay
initially. With no active slides, a designed placeholder appears instead.

The homepage shows the next published gathering, published history excerpts,
the two most recent eligible albums with active photos, published FAQs, and the
profile's contact links. Our Story now has its own page at `/our-story/` with the
history wheel, purpose/beliefs from Club profiles, and active organizer cards.
History milestones follow display order (lower first); set that order to match
the chronology you want visitors to follow. Only published milestones appear.
Upload an image and alt text on each milestone or organizer to replace its placeholder.
Press the wheel to open the horizontal timeline, then scroll through the years or use
the chapter selector. New milestones extend the timeline without crowding the wheel.
Reduced-motion preferences are respected. Without JavaScript,
all chapters remain readable in order. Events and contact still link to homepage
sections until their dedicated pages are built. The generated
admin mockup is a visual reference, not the current Django admin theme.
