# R&D 23: MCP Tool Expansion

## Status: Research

## What Is This?

Additional Model Context Protocol (MCP) tools to expand Mindrian's capabilities.

## Why Implement This?

### Current State
- Limited tool set (Tavily search, internal tools)
- No external integrations
- Manual data entry for context

### Solution: MCP Expansion
- Database querying tools
- Code execution sandbox
- Document generation
- External service integrations

## Potential MCP Tools

### 1. Database Tools

```python
# Query user's own data sources
class DatabaseQueryTool:
    """Query external databases for evidence gathering."""

    async def query(self, connection_string: str, query: str) -> list[dict]:
        # Support PostgreSQL, MySQL, MongoDB
        pass
```

**Use Cases:**
- Pull customer data for JTBD analysis
- Query sales metrics for S-Curve timing
- Access user research databases

### 2. Code Execution Sandbox

```python
class CodeExecutionTool:
    """Execute Python code in isolated sandbox."""

    async def execute(self, code: str, timeout: int = 30) -> dict:
        # Use E2B or Modal for sandboxed execution
        pass
```

**Use Cases:**
- Data analysis scripts
- Visualization generation
- Calculation verification

### 3. Document Generation

```python
class DocumentGenerator:
    """Generate formatted documents from structured data."""

    async def generate_slides(self, content: dict) -> bytes:
        # Generate PowerPoint/Google Slides
        pass

    async def generate_report(self, content: dict, format: str) -> bytes:
        # Generate PDF, DOCX, or Markdown
        pass
```

**Use Cases:**
- Workshop summary presentations
- Problem statement documents
- Research reports

### 4. Calendar/Scheduling

```python
class CalendarTool:
    """Schedule follow-up sessions and reminders."""

    async def create_event(self, title: str, datetime: str, attendees: list[str]) -> dict:
        # Google Calendar / Outlook integration
        pass
```

**Use Cases:**
- Schedule validation interviews
- Set assumption review reminders
- Book team workshops

### 5. Notion/Docs Integration

```python
class NotionTool:
    """Sync insights to Notion workspace."""

    async def create_page(self, database_id: str, content: dict) -> str:
        # Create page in Notion database
        pass

    async def update_page(self, page_id: str, content: dict) -> None:
        pass
```

**Use Cases:**
- Export opportunities to Notion
- Sync workshop progress
- Archive validated problems

### 6. Visualization Tools

```python
class VisualizationTool:
    """Generate diagrams and charts."""

    async def create_mermaid(self, diagram_type: str, content: str) -> str:
        # Generate Mermaid diagrams
        pass

    async def create_chart(self, data: dict, chart_type: str) -> bytes:
        # Generate Plotly/Chart.js visualizations
        pass
```

**Use Cases:**
- Problem hierarchy diagrams
- S-Curve visualizations
- DIKW pyramid charts

## MCP Configuration

```toml
# .chainlit/config.toml
[features.mcp]
enabled = true

[features.mcp.servers.database]
command = "python"
args = ["-m", "mcp_database_server"]
env = { DATABASE_URL = "..." }

[features.mcp.servers.notion]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-notion"]
env = { NOTION_API_KEY = "..." }
```

## Research Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [E2B](https://e2b.dev/) - Code sandbox
- [Modal](https://modal.com/) - Serverless compute

## Security Considerations

- OAuth scopes for external services
- Sandbox isolation for code execution
- Rate limiting per tool
- Audit logging for sensitive operations

## Estimated Effort

- Per tool: 8-15 hours
- Full suite: 60-100 hours

## Priority Tools

| Tool | Priority | Effort | Impact |
|------|----------|--------|--------|
| Notion sync | HIGH | 12h | User workflow integration |
| Code sandbox | MEDIUM | 15h | Data analysis capability |
| Visualization | MEDIUM | 10h | Better presentations |
| Calendar | LOW | 8h | Nice-to-have |
| Database | LOW | 15h | Advanced users only |

## Status Checklist

- [ ] Survey existing MCP servers
- [ ] Prioritize tool development
- [ ] Implement Notion integration
- [ ] Implement visualization tools
- [ ] Security review
- [ ] User documentation

---

*Created: 2026-01-30*
