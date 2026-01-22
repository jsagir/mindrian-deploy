# PWS Audiobook Content - Audio URLs Needed

## What Is This?

The audiobook chapter system is **implemented** in `utils/media.py`, but the actual audio file URLs need to be added.

## Why This Matters

- Users can click "📖 Listen to Chapter" button
- System will find contextually relevant chapters
- But no audio will play until URLs are configured

## Current State

The `AUDIOBOOK_CHAPTERS` dict in `utils/media.py` has placeholders:

```python
AUDIOBOOK_CHAPTERS = {
    "pws_foundation": {
        "chapter_1": {
            "title": "Introduction to Problems Worth Solving",
            "url": "",  # <-- NEEDS URL
            "duration": "15:00",
            "keywords": ["problem", "worth solving", "introduction"],
        },
        # ...
    },
    # ...
}
```

## What's Needed

### Option 1: Upload to Supabase Storage
1. Record or obtain PWS audiobook chapters
2. Upload to Supabase Storage bucket
3. Get public URLs
4. Add URLs to `AUDIOBOOK_CHAPTERS`

### Option 2: External Hosting
1. Host audio files on YouTube, Vimeo, or CDN
2. Add URLs to `AUDIOBOOK_CHAPTERS`

## Audio Content Needed

| Topic | Chapters | Status |
|-------|----------|--------|
| PWS Foundation | 3 chapters | URLs needed |
| Trending to Absurd | 3 chapters | URLs needed |
| Jobs to Be Done | 3 chapters | URLs needed |
| S-Curve | 3 chapters | URLs needed |
| Ackoff's Pyramid | 3 chapters | URLs needed |
| Red Teaming | 3 chapters | URLs needed |

## How to Add URLs

### Using set_audiobook_chapter()
```python
from utils.media import set_audiobook_chapter

set_audiobook_chapter(
    topic="pws_foundation",
    chapter_id="chapter_1",
    url="https://your-storage.supabase.co/audio/pws_ch1.mp3"
)
```

### Direct Edit
Edit `utils/media.py` line ~590:
```python
"pws_foundation": {
    "chapter_1": {
        "title": "Introduction to Problems Worth Solving",
        "url": "https://actual-url-here.mp3",  # ADD URL
        ...
    },
}
```

## Recording Guidelines

If recording new content:
- Format: MP3, 128kbps minimum
- Length: 8-15 minutes per chapter
- Voice: Clear, professional, Larry-style teaching
- Content: Match chapter titles and keywords

## Status

- [x] Code implementation complete
- [x] Button integrated in UI
- [ ] Audio content recorded/obtained
- [ ] URLs added to config
- [ ] Testing with actual audio
