# Category template: Collaborative / Real-time Platforms

Use this as the **shared family shape**. Every generated prompt must feel like a
distinct product in this family — not a generic chat demo or identical whiteboard clone.

## Product family intent

Build a multi-user collaborative system where state changes made by one participant
become visible to others with low latency. The product should support identity,
spaces/rooms (or equivalent), presence, conflict-aware updates, and at least one
primary collaborative artifact (canvas, messages, documents, boards, etc.).

## Identity & positioning (must invent uniquely each run)

- Product name and one-sentence pitch
- Specific audience (e.g. design studios, study groups, incident responders, teachers)
- Collaboration metaphor (room, board, channel, session, workspace)
- One domain twist that is uncommon in tutorial apps (e.g. timed critique rounds,
  sticky voice notes, role-gated drawing layers, moderated guest links)

## Required capability areas

### Spaces & membership
- Create/join spaces with invite or share codes
- Roles (at least owner/member/guest or equivalent)
- Soft limits: max concurrent participants per space
- Reconnect behavior after network blips

### Presence & awareness
- Online/offline (or idle) indicators
- Cursor/presence markers when relevant to the artifact
- Activity feed or lightweight event log inside the space

### Collaborative artifact
Define ONE primary artifact deeply (do not shallowly list five):
- If canvas: freehand, shapes, colors, eraser, undo/redo, export
- If chat: channels/DMs, mentions, unread, attachments
- If board: cards/columns, assignees, comments
- Conflict policy: last-write-wins vs operational transform vs lock sections — pick one and state it

### Persistence & history
- Durable storage for spaces and artifact state
- Snapshot or history that survives refresh
- Optional version restore or clear/reset with confirmation

### Realtime transport
- Explicit realtime channel (WebSocket / SSE / Socket.IO / similar)
- Server authority for membership and persistence
- Client optimistic UI allowed if reconciliation is defined

## UX expectations

- Responsive layout suitable for laptop + tablet
- Empty states that teach first actions
- Clear connection status (connected / reconnecting / offline)
- Accessible controls for primary actions (create space, draw/send, invite)

## Data model expectations (specialize names)

Sketch entities the implementation should materialize, e.g.:
User, Space, Membership, PresenceSession, ArtifactObject, ArtifactEvent, Invite.

## Quality & reliability

- Meaningful validation on joins and mutations
- Rate-limit or debounce spammy realtime events where sensible
- Graceful degradation messaging when realtime is down
- Automated tests for auth/membership and at least one collaborative mutation path

## Documentation & deliverables

- README with local run steps
- Architecture note explaining realtime flow
- Seed script or fixture for a demo space (optional but preferred)

## Constraints & non-goals

- Not a full Google Docs OT clone unless the seed demands it
- Not a social network with feeds/followers
- Avoid placeholder “Room 1 / User A” only demos — require realistic naming and workflows

## Acceptance criteria checklist (customize)

- [ ] Multiple users can join the same space
- [ ] Concurrent edits/events are visible without full page reload
- [ ] Refresh restores durable state
- [ ] Roles/permissions enforce at least one restricted action
- [ ] Reconnect path is documented and demonstrable
- [ ] Tests cover core membership + artifact mutation
- [ ] README runs the stack locally

## Variation axes (pick different combinations each run)

Audience niche · artifact type · moderation style · invite model · presence richness ·
export formats · offline behavior · mobile emphasis · admin analytics light/heavy

## Anti-clone rules

Do **not** emit a near-copy of “Socket.IO whiteboard tutorial”. Change domain language,
feature mix, and workflows so traces diversify across synthetic runs.
