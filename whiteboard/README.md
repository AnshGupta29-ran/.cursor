# Collab Whiteboard

Real-time collaborative whiteboard: React + TypeScript client, Node/Express +
Socket.IO server. Multiple users draw in the same room with colors, brush
sizes, shapes, eraser, undo/redo, clear, and PNG export.

## Architecture

**Op-based sync.** Each committed stroke is an operation `{ id, userId, kind,
style, points }`. The server holds the canonical ordered op log per room and
broadcasts new ops; the canvas is a pure function of the log. Consequences:

- **Join / reconnect = full state replay.** The server sends the whole op log;
  the client replays it. No delta protocol, no missed-event recovery — this is
  what makes reconnecting graceful.
- **Undo removes YOUR stroke, not the LAST stroke.** A naive global stack would
  let Alice's undo eat Bob's newer stroke. Server-side `undo(userId)` splices
  the caller's most recent op and broadcasts `op:remove`; `redo` re-appends.
- **Live segments ≠ ops.** In-progress freehand segments broadcast separately
  (never stored) so peers watch strokes form in real time; only pointerup
  commits an op. Shape previews never leave the client until commit.

**Canvas rendering lives outside React.** pointermove fires 60+/s — the wrong
granularity for React re-renders. `Board` owns canvas refs and calls renderer
functions directly; React renders only toolbars/presence (DOM concerns).

**Two stacked canvases.** Board canvas holds committed strokes; a transparent
overlay holds the in-progress shape preview, cleared per pointermove — the
committed board is never touched until pointerup.

**DPR-aware.** Points stored in CSS pixels; backing store scaled by
devicePixelRatio. Sharp on retina, zero bookkeeping in draw code.

## Protocol (Socket.IO)

| Event | Direction | Payload |
|---|---|---|
| `room:join` | c→s | `{ roomId, name }` |
| `room:state` | s→c | `{ ops, users }` full replay |
| `draw:segment` | both | live in-progress segment (not stored) |
| `op:add` | both | committed stroke |
| `op:undo` / `op:remove` | c→s / s→all | undo own stroke |
| `op:redo` | c→s | s→all `op:add` re-append |
| `op:clear` | both | wipe room |
| `user:joined` / `user:left` | s→c | presence |

Server validates every op at the socket boundary and stamps `userId` from the
socket — clients never name their own user.

## Run

```bash
npm run install:all
npm run dev:server   # http://localhost:3001
npm run dev:client   # http://localhost:5173
```

Open `http://localhost:5173/?room=anything` in two tabs to collaborate.

Production: `npm run build` (type-check + vite build), then `npm start` —
the server serves `client/dist` on :3001.

## Shortcuts

`P` pen · `E` eraser · `L` line · `R` rect · `C` circle · `Ctrl+Z` undo ·
`Ctrl+Shift+Z` / `Ctrl+Y` redo

## Known scope limits (documented, not built)

- In-memory rooms — restart wipes boards. Swap `RoomStore` for Redis to scale.
- Redo button enablement is approximated client-side; the server is authoritative.
- No auth — anyone with the room URL can join.
