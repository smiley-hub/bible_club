# Demo data

The local demo contains 3 active slides, 4 published events (2 future and 2 past),
2 albums with 3 photo entries each, 3 history milestones, 3 FAQs, 2 organizer
placeholders, and a club profile if none already exists.

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo --download-images
```

Dates are relative to the first run. Repeated runs preserve matching records,
including edited dates, answers, and publication states. No user accounts are
created. Matching uses demo titles/questions, event slugs, and album/photo links;
renaming those identifying fields and rerunning can create a new demo entry.

All event dates, milestones, and venue information are illustrative. `hello@example.com`
is a reserved example address, not a working club inbox. Replace it in Club profiles.
You can hide, edit, or delete demo records through admin before adding real content.
Do not publish the demo as factual club information.

## Images

Stock images are stored in ignored `media/demo/`; no generated mockups were edited.
They are not photographs of METU Bible Club, and captions explicitly say so.

Sources (Unsplash):

- `study.jpg`: https://images.unsplash.com/photo-1522202176988-66273c2fd55f
- `community.jpg`: https://images.unsplash.com/photo-1523240795612-9a054b0db644
- `together.jpg`: https://images.unsplash.com/photo-1511988617509-a57c8a288659
- License: https://unsplash.com/license

Images are shared by several demo records. Replacing a record's image in admin
does not change the others. Do not delete the shared files while still referenced.
