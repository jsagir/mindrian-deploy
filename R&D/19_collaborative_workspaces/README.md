# R&D 19: Collaborative Workspaces

## Status: Research

## What Is This?

Multi-user workshop sessions where teams can collaborate on PWS methodology in real-time.

## Why Implement This?

### Current State
- Single-user sessions only
- No shared artifact editing
- Teams can't collaborate live
- No role-based contributions

### Solution: Collaborative Workspaces
- Multiple users in same workshop
- Shared problem statements and insights
- Role-based permissions (facilitator, participant, observer)
- Real-time updates across clients

## Features

### 1. Session Sharing
```python
# Create shareable workspace
workspace = await create_workspace(
    name="Q1 Strategy Workshop",
    bot_id="ackoff",
    owner_id="user_123"
)
share_link = f"https://mindrian.app/join/{workspace.id}"
```

### 2. Role-Based Access
| Role | Can Chat | Can Edit | Can Progress | Can Invite |
|------|----------|----------|--------------|------------|
| Owner | Yes | Yes | Yes | Yes |
| Facilitator | Yes | Yes | Yes | Yes |
| Participant | Yes | Limited | No | No |
| Observer | No | No | No | No |

### 3. Shared Artifacts
- Problem statement (collaborative editing)
- Assumption board (add/challenge/validate)
- Opportunity bank (shared)
- Progress tracking (synchronized)

### 4. Presence Indicators
- Who's online
- Who's typing
- Last activity
- Active section

## Technical Considerations

### Chainlit WebSocket
- Chainlit uses WebSocket for real-time
- Need custom room management
- Message broadcasting to room members

### Conflict Resolution
- Last-write-wins vs. operational transforms
- Locking mechanisms for edits
- Merge strategies for assumptions

### Scalability
- Session limits per workspace
- Message rate limiting
- Storage limits per team

## Research Resources

- [Chainlit Copilots](https://docs.chainlit.io/concepts/copilot)
- [Liveblocks](https://liveblocks.io/) - Real-time collaboration
- [Y.js](https://yjs.dev/) - CRDT for collaborative editing
- [Hocuspocus](https://hocuspocus.dev/) - WebSocket backend

## Estimated Effort

- Design: 15-20 hours
- Implementation: 50-80 hours
- Testing: 20-30 hours

**Note:** This is a significant undertaking requiring Chainlit customization.

## Status Checklist

- [ ] Research Chainlit multi-user patterns
- [ ] Design workspace schema
- [ ] Implement session sharing
- [ ] Role-based permissions
- [ ] Real-time sync
- [ ] Conflict resolution
- [ ] UI for collaboration
- [ ] Testing

---

*Created: 2026-01-30*
