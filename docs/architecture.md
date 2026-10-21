# Website structure review

## Current state

The existing Django structure fits the approved METU Bible Club website.
Keep the `core` and `events` apps, server-rendered templates, Django admin,
and local media storage. No separate frontend service or accounts app is needed.

Implemented today: environment-based settings, SQLite, Django authentication,
content models and migrations, leader permissions, admin content/photo editing,
upload validation, publication querysets, a responsive homepage, static/media
configuration, and saved mockups. The homepage uses local Lora/Source Sans 3 fonts,
active photo slides, upcoming events, history excerpts, albums, FAQs, and contact
links. Separate public pages, the full history wheel, contact-form handling,
sitemap, and robots route are not implemented yet.
Responsive image derivatives and orphaned-file cleanup remain future work.

## App responsibilities and planned models

### core

| Model | Purpose and main fields |
| --- | --- |
| ClubProfile | One editable club profile: name, welcome text, purpose, beliefs, meeting information, contact email, social URL. Prevent duplicate profiles in admin. |
| HomeSlide | Image, required alt text, optional caption, display order, active flag. Leaders can upload, replace, reorder, hide, or remove slides. |
| HistoryMilestone | Title, year, story, optional photo and alt text, display order, published flag. Supplies the history wheel and an accessible chronological list. |
| Organizer | Name, role, optional portrait and alt text, display order, active flag. |
| FAQ | Question, answer, display order, published flag. |

`core` owns Home, Our Story, Get in Touch, shared club information, and static-page
sitemap entries. Use Django forms for contact validation. Contact delivery is a
separate integration; use a local console email backend during development and
configure actual delivery before presenting the form as operational in production.
No contact-message database is needed initially.

### events

| Model | Purpose and main fields |
| --- | --- |
| Event | Title, unique slug, description, optional start/end times, venue, directions URL, optional cover and alt text, category, draft/published/cancelled status. |
| EventAlbum | One optional album per event: title, recap, optional cover and alt text, published flag. Its event supplies the date and URL slug. |
| EventPhoto | Album relation, image, required alt text, optional caption, display order, active flag. |

An event may exist without an album. An album may contain many photos. Keeping
album publication separate allows leaders to prepare pictures before sharing them.
Use the event cover as an album-cover fallback where appropriate.

Drafts are private. Future dated events appear under upcoming gatherings;
undated published events appear separately as dates to be announced. Past albums
only appear when both the event and album are published. Explicitly cancelled
events retain an explanatory public detail page but never become the next-meeting
recommendation. Validate end time after start time. Order dated upcoming events
chronologically and past albums newest first.

## Public routes and templates to implement

| Route | View owner | Template |
| --- | --- | --- |
| `/` | core | `core/home.html` |
| `/our-story/` | core | `core/our_story.html` |
| `/events/` | events | `events/event_list.html` |
| `/events/<slug>/` | events | `events/event_detail.html` |
| `/events/<slug>/photos/` | events | `events/album_detail.html` |
| `/contact/` | core | `core/contact.html` |
| `/admin/` | Django admin | Django admin templates; optional theme later |
| `/robots.txt` | core | `robots.txt` |
| `/sitemap.xml` | Django sitemap framework | Generated from public routes and content |

Use a contact success state instead of another full page. Provide a shared 404
template. Public detail views must enforce publication status, including direct
requests to draft URLs. Add calendar downloads only for confirmed dated events.

## Target file layout

This is the implementation plan; files listed here do not all exist yet.

```text
config/                 settings, root routes, server entry points
core/
  models.py             club profile, slides, milestones, organizers, FAQs
  admin.py              leader editing and ordering
  forms.py              contact validation
  views.py              home, story, contact, robots
  urls.py
  context_processors.py shared club details
  sitemaps.py            public static-page entries
  tests.py
  migrations/
events/
  models.py             events, albums, photos
  admin.py              event editing and album photo inlines
  views.py              list, event details, photo album
  urls.py
  sitemaps.py            published event/album entries
  tests.py
  migrations/
templates/
  base.html             metadata, fonts, shared layout
  includes/             navigation, footer, reusable event cards
  core/                 home, our_story, contact
  events/               event_list, event_detail, album_detail
  robots.txt
  404.html
static/
  css/                  shared design tokens and responsive styles
  js/                   navigation, slideshow, history wheel, photo viewer
  fonts/                Lora and Source Sans 3 with license files
  images/               fixed design assets
media/                  runtime uploads; ignored by Git
  homepage/
  history/
  organizers/
  events/
docs/                   architecture and implementation notes
design/                 approved visual references
```

Keep tests in their owning apps for now. Do not create a separate test tree or
extra empty apps simply to match a larger-project structure.

## Interaction and storage requirements

- Slideshow: leader-controlled order and visibility, previous/next buttons,
  position controls, pause for autoplay, reduced-motion support, and a useful
  single-image/empty state. Load the first photo promptly and defer later images.
- History wheel: click/tap and keyboard controls; do not require dragging. Render
  the history in HTML so it remains readable without JavaScript.
- Gallery: thumbnails link to larger photos; an enhanced viewer supports keyboard
  navigation, Escape to close, and focus return.
- Uploads: validate image type and size, resize for intended display, preserve
  useful alt text, and avoid serving full-size originals for every thumbnail.
- Store image paths and metadata in the database; store actual files in media
  storage. Production needs a persistent disk and backups of both.
- Replacing or deleting an image record does not automatically clean up every old
  file. Plan explicit orphan cleanup without deleting files still in use.
- Use staff accounts and Django model permissions for leaders. Public visitors
  have no login requirement. Styling the admin is separate from authentication.
- Sitemap entries contain only published pages. Robots instructions are not
  access control; admin protection comes from authentication and permissions.

## Implementation order

1. Content models, migrations, admin editing, image validation, publication tests.
2. Shared layout, fonts, responsive navigation, and homepage with managed slides.
3. Our Story with managed milestones and history-wheel enhancement.
4. Event list/details and past-event photo albums.
5. Contact form and delivery configuration, FAQ, metadata, sitemap, robots.
6. Mobile/keyboard checks, image performance, deployment and backup setup.

Reuse the approved mockups. Do not regenerate or edit the concept images.
