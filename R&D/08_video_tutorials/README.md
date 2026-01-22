# Video Tutorials - Workshop Video URLs Needed

## What Is This?

The video tutorial system is **implemented** in `utils/media.py`, but the actual video URLs need to be added.

## Why This Matters

- Users can click "🎬 Watch Video" button
- System shows phase-specific tutorial videos
- But no video will play until URLs are configured

## Current State

The `WORKSHOP_VIDEOS` dict in `utils/media.py` has placeholders:

```python
WORKSHOP_VIDEOS = {
    "larry": {
        "intro": "",  # <-- NEEDS URL
        "welcome": "",
    },
    "tta": {
        "intro": "",  # <-- NEEDS URL
        "phase_1": "",
        "phase_2": "",
        # ...
    },
    # ...
}
```

## What's Needed

### Supported Video Sources
- YouTube (any format): `https://youtube.com/watch?v=VIDEO_ID`
- YouTube short: `https://youtu.be/VIDEO_ID`
- Vimeo: `https://vimeo.com/VIDEO_ID`
- Direct MP4: `https://example.com/video.mp4`
- Supabase Storage: Upload and use public URL

## Video Content Needed

### Larry (General)
| Phase | Topic | Duration | Status |
|-------|-------|----------|--------|
| intro | Welcome to Mindrian | 2-3 min | URL needed |
| welcome | How to use Larry | 3-5 min | URL needed |

### Trending to the Absurd (TTA)
| Phase | Topic | Duration | Status |
|-------|-------|----------|--------|
| intro | What is TTA? | 3-5 min | URL needed |
| phase_1 | Identifying Trends | 5-7 min | URL needed |
| phase_2 | Extrapolation | 5-7 min | URL needed |
| phase_3 | Absurd Scenarios | 5-7 min | URL needed |
| phase_4 | Implications | 5-7 min | URL needed |
| phase_5 | Opportunities | 5-7 min | URL needed |

### Jobs to Be Done (JTBD)
| Phase | Topic | Duration | Status |
|-------|-------|----------|--------|
| intro | What is JTBD? | 3-5 min | URL needed |
| phase_1 | Job Discovery | 5-7 min | URL needed |
| phase_2 | Job Mapping | 5-7 min | URL needed |
| phase_3 | Solution Fit | 5-7 min | URL needed |

### S-Curve Analysis
| Phase | Topic | Duration | Status |
|-------|-------|----------|--------|
| intro | Understanding S-Curves | 3-5 min | URL needed |
| phase_1 | Technology Assessment | 5-7 min | URL needed |
| phase_2 | Curve Positioning | 5-7 min | URL needed |
| phase_3 | Timing Strategy | 5-7 min | URL needed |

### Red Teaming
| Phase | Topic | Duration | Status |
|-------|-------|----------|--------|
| intro | Devil's Advocacy | 3-5 min | URL needed |
| phase_1 | Assumption Identification | 5-7 min | URL needed |
| phase_2 | Attack Scenarios | 5-7 min | URL needed |
| phase_3 | Mitigation | 5-7 min | URL needed |

### Ackoff's Pyramid (DIKW)
| Phase | Topic | Duration | Status |
|-------|-------|----------|--------|
| intro | The DIKW Pyramid | 3-5 min | URL needed |
| phase_1 | Team Onboarding | 3-5 min | URL needed |
| phase_2 | Data Collection | 5-7 min | URL needed |
| phase_3 | Information Synthesis | 5-7 min | URL needed |
| phase_4 | Knowledge Building | 5-7 min | URL needed |
| phase_5 | Understanding | 5-7 min | URL needed |
| phase_6 | Wisdom Application | 5-7 min | URL needed |
| phase_7 | Action Planning | 5-7 min | URL needed |
| phase_8 | Debrief | 3-5 min | URL needed |

## How to Add URLs

### Using set_workshop_video()
```python
from utils.media import set_workshop_video

set_workshop_video("tta", "intro", "https://youtube.com/watch?v=YOUR_VIDEO_ID")
set_workshop_video("tta", "phase_1", "https://youtu.be/SHORT_ID")
```

### Direct Edit
Edit `utils/media.py` line ~390:
```python
WORKSHOP_VIDEOS = {
    "tta": {
        "intro": "https://youtube.com/watch?v=ACTUAL_VIDEO_ID",  # ADD URL
        "phase_1": "https://youtu.be/PHASE1_VIDEO",
        ...
    },
}
```

## Video Production Guidelines

If creating new content:
- Format: MP4 or YouTube upload
- Resolution: 1080p minimum
- Length: 3-7 minutes per video (attention span)
- Style: Screen recording with voiceover, or talking head
- Content: Match phase objectives

## Quick Win

If you have existing course videos, map them to phases:
1. Find relevant segments from JHU PWS course recordings
2. Upload to YouTube (unlisted if needed)
3. Add URLs to config

## Status

- [x] Code implementation complete
- [x] Button integrated in UI
- [ ] Video content recorded/obtained
- [ ] URLs added to config
- [ ] Testing with actual videos
