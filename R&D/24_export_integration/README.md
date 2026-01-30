# R&D 24: Export and Integration

## Status: Research

## What Is This?

Better output formats and integrations with external tools for seamless workflow continuation.

## Why Implement This?

### Current State
- Export limited to Markdown files
- No direct integration with productivity tools
- Manual copy-paste for external use

### Solution: Rich Exports
- Multiple format options
- Direct tool integrations
- Structured data exports

## Export Formats

### 1. Presentation Export

```python
async def export_to_slides(workshop_data: dict) -> bytes:
    """Generate presentation from workshop insights."""

    slides = [
        TitleSlide(
            title=workshop_data["problem_statement"],
            subtitle=f"PWS Workshop: {workshop_data['bot_used']}"
        ),
        ContentSlide(
            title="Key Insights",
            bullets=workshop_data["insights"]
        ),
        ContentSlide(
            title="Validated Assumptions",
            bullets=workshop_data["validated_assumptions"]
        ),
        ContentSlide(
            title="Open Questions",
            bullets=workshop_data["open_questions"]
        ),
        ContentSlide(
            title="Next Steps",
            bullets=workshop_data["recommendations"]
        )
    ]

    return generate_pptx(slides)
```

### 2. Notion Page Export

```python
async def export_to_notion(
    workshop_data: dict,
    database_id: str,
    api_key: str
) -> str:
    """Create Notion page from workshop."""

    page = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": workshop_data["title"]}}]},
            "Status": {"select": {"name": workshop_data["status"]}},
            "Date": {"date": {"start": workshop_data["date"]}},
            "Bot": {"select": {"name": workshop_data["bot_used"]}}
        },
        "children": format_notion_blocks(workshop_data)
    }

    return notion_client.pages.create(**page)
```

### 3. Google Docs Export

```python
async def export_to_gdocs(
    content: str,
    title: str,
    folder_id: str
) -> str:
    """Create Google Doc from workshop content."""

    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    # Insert content
    requests = [
        {"insertText": {"location": {"index": 1}, "text": content}}
    ]
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests}
    ).execute()

    return f"https://docs.google.com/document/d/{doc_id}"
```

### 4. Miro/FigJam Export

```python
async def export_to_miro(
    assumptions: list[dict],
    board_id: str
) -> None:
    """Create assumption cards on Miro board."""

    for assumption in assumptions:
        miro_client.create_sticky_note(
            board_id=board_id,
            content=assumption["text"],
            color=get_color_by_status(assumption["status"]),
            position=calculate_position(assumption)
        )
```

### 5. Structured Data Export

```python
@dataclass
class WorkshopExport:
    id: str
    title: str
    bot_used: str
    date: str
    problem_statement: str
    assumptions: list[AssumptionExport]
    insights: list[InsightExport]
    opportunities: list[OpportunityExport]
    next_steps: list[str]
    conversation_summary: str

def export_json(workshop: WorkshopExport) -> str:
    return workshop.model_dump_json(indent=2)

def export_csv(workshops: list[WorkshopExport]) -> str:
    # Flatten for spreadsheet analysis
    pass
```

## Integration Points

### OAuth Integrations

| Service | OAuth Scope | Use Case |
|---------|-------------|----------|
| Google | docs, drive, calendar | Doc export, scheduling |
| Notion | pages:write | Page creation |
| Miro | boards:write | Visual collaboration |
| Slack | chat:write | Team notifications |

### Webhook Integrations

```python
async def send_webhook(
    url: str,
    event: str,
    data: dict
) -> None:
    """Send workshop events to external systems."""

    payload = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)
```

**Events:**
- `workshop.completed`
- `assumption.validated`
- `opportunity.created`
- `grade.assigned`

## UI for Export

```python
@cl.action_callback("export_workshop")
async def on_export(action: cl.Action):
    format = action.payload.get("format", "markdown")

    if format == "markdown":
        file = create_markdown_export(workshop_data)
    elif format == "slides":
        file = await export_to_slides(workshop_data)
    elif format == "notion":
        url = await export_to_notion(workshop_data)
        await cl.Message(f"Created Notion page: {url}").send()
        return
    elif format == "json":
        file = export_json(workshop_data)

    await cl.Message(
        content="Export ready!",
        elements=[cl.File(name=f"export.{format}", content=file)]
    ).send()
```

## Research Resources

- [python-pptx](https://python-pptx.readthedocs.io/) - PowerPoint generation
- [Notion API](https://developers.notion.com/)
- [Google Docs API](https://developers.google.com/docs/api)
- [Miro API](https://developers.miro.com/)

## Estimated Effort

| Integration | Effort | Priority |
|-------------|--------|----------|
| Enhanced Markdown | 4h | HIGH |
| PowerPoint | 12h | MEDIUM |
| Notion | 8h | HIGH |
| Google Docs | 10h | MEDIUM |
| Miro | 10h | LOW |
| Webhooks | 6h | MEDIUM |

## Status Checklist

- [ ] Enhanced Markdown templates
- [ ] PowerPoint generation
- [ ] Notion OAuth flow
- [ ] Notion page creation
- [ ] Google OAuth flow
- [ ] Google Docs creation
- [ ] Webhook system
- [ ] Export UI

---

*Created: 2026-01-30*
