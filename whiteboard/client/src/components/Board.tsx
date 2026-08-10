import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { BoardSocket, ConnStatus } from '../socket';
import type { Point, RemoteSegment, RoomState, Stroke, Tool, UserInfo } from '../types';
import { drawSegment, drawStroke, exportPNG, redrawAll } from '../canvas/renderer';
import { Toolbar } from './Toolbar';

interface Props {
  socket: BoardSocket;
  roomId: string;
  name: string;
  onLeave: () => void;
}

// Board owns the canvases and ALL drawing state in refs (not React state):
// pointermove fires far too often for re-renders. React state is used only
// for things that render as DOM — tool selection, presence, connection status.
export function Board({ socket, roomId, name, onLeave }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const boardRef = useRef<HTMLCanvasElement>(null);   // committed strokes
  const overlayRef = useRef<HTMLCanvasElement>(null); // shape preview only

  const opsRef = useRef<Stroke[]>([]);        // mirror of the server op log
  const drawing = useRef<{ stroke: Stroke; last: Point } | null>(null);
  const remoteLive = useRef<Map<string, { kind: string; style: any }>>(new Map());

  const [tool, setTool] = useState<Tool>('pen');
  const [color, setColor] = useState('#1f2933');
  const [size, setSize] = useState(4);
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [status, setStatus] = useState<ConnStatus>('connecting');
  const [history, setHistory] = useState({ undo: false, redo: false });

  // tool/color/size in refs too — pointer handlers read them without stale closures
  const toolRef = useRef(tool); toolRef.current = tool;
  const colorRef = useRef(color); colorRef.current = color;
  const sizeRef = useRef(size); sizeRef.current = size;

  const boardCtx = () => boardRef.current!.getContext('2d')!;
  const overlayCtx = () => overlayRef.current!.getContext('2d')!;

  const fullRedraw = useCallback(() => {
    const c = boardRef.current!;
    redrawAll(boardCtx(), opsRef.current, c.width, c.height);
  }, []);

  const refreshHistory = useCallback((usersNow: UserInfo[]) => {
    const myId = socketIdOf(socket);
    const ops = opsRef.current;
    setHistory({
      undo: ops.some(o => o.userId === myId),
      // redo availability is server-side knowledge; we approximate: enabled after we undo something.
      redo: (refreshHistory as any)._redo ?? false
    });
  }, [socket]);

  // --- Canvas sizing: ResizeObserver on the wrapper, DPR-aware. -------------
  // Changing canvas.width clears it, so every resize is followed by a replay.
  useEffect(() => {
    const wrap = wrapRef.current!;
    const fit = () => {
      const dpr = window.devicePixelRatio || 1;
      const { clientWidth: w, clientHeight: h } = wrap;
      for (const c of [boardRef.current!, overlayRef.current!]) {
        c.width = Math.round(w * dpr);
        c.height = Math.round(h * dpr);
        c.style.width = `${w}px`;
        c.style.height = `${h}px`;
        c.getContext('2d')!.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
      fullRedraw();
    };
    const ro = new ResizeObserver(fit);
    ro.observe(wrap);
    fit();
    return () => ro.disconnect();
  }, [fullRedraw]);

  // --- Socket wiring ----------------------------------------------------------
  useEffect(() => {
    socket.setHandlers({
      onState: (s: RoomState) => {
        // Full replay: join AND every reconnect land here. This is the entire
        // reconnection story — the canvas is a pure function of the op log.
        opsRef.current = s.ops;
        setUsers(s.users);
        fullRedraw();
        refreshHistory(s.users);
      },
      onOpAdd: (s: Stroke) => {
        opsRef.current = [...opsRef.current, s];
        drawStroke(boardCtx(), s);
        refreshHistory(users);
      },
      onOpRemove: (strokeId: string) => {
        opsRef.current = opsRef.current.filter(o => o.id !== strokeId);
        (refreshHistory as any)._redo = true;
        fullRedraw();
        refreshHistory(users);
      },
      onClear: () => {
        opsRef.current = [];
        (refreshHistory as any)._redo = false;
        fullRedraw();
        refreshHistory(users);
      },
      onSegment: (seg: RemoteSegment) => {
        remoteLive.current.set(seg.userId, { kind: seg.kind, style: seg.style });
        drawSegment(boardCtx(), seg.kind, seg.style, seg.segment[0], seg.segment[1]);
      },
      onUserJoined: (u: UserInfo) => setUsers(prev => [...prev.filter(x => x.id !== u.id), u]),
      onUserLeft: (id: string) => { remoteLive.current.delete(id); setUsers(prev => prev.filter(x => x.id !== id)); },
      onStatus: setStatus
    });
    socket.join(roomId, name);
  }, [socket, roomId, name, fullRedraw, refreshHistory, users]);

  // --- Pointer handling --------------------------------------------------------
  const toLocal = (e: React.PointerEvent): Point => {
    const r = boardRef.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };

  const strokeKind = () => (toolRef.current === 'pen' ? 'freehand'
    : toolRef.current === 'eraser' ? 'erase' : toolRef.current) as Stroke['kind'];

  const onPointerDown = (e: React.PointerEvent) => {
    if (status !== 'online') return;
    boardRef.current!.setPointerCapture(e.pointerId);
    const p = toLocal(e);
    const stroke: Stroke = {
      id: crypto.randomUUID(),
      userId: socketIdOf(socket),
      kind: strokeKind(),
      style: { color: colorRef.current, size: sizeRef.current },
      points: [p]
    };
    drawing.current = { stroke, last: p };
    if (stroke.kind === 'freehand' || stroke.kind === 'erase') {
      drawSegment(boardCtx(), stroke.kind, stroke.style, p, p); // dot on click
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const d = drawing.current;
    if (!d) return;
    const p = toLocal(e);
    const { stroke } = d;
    const last = d.last;

    if (stroke.kind === 'freehand' || stroke.kind === 'erase') {
      drawSegment(boardCtx(), stroke.kind, stroke.style, last, p);
      socket.sendSegment({ userId: stroke.userId, strokeId: stroke.id, kind: stroke.kind, style: stroke.style, segment: [last, p] });
      stroke.points.push(p);
      d.last = p;
    } else {
      // Shape preview lives on the overlay canvas — erased each move, so the
      // committed board is never touched until pointerup commits the shape.
      stroke.points[1] = p;
      const c = overlayRef.current!;
      overlayCtx().clearRect(0, 0, c.clientWidth, c.clientHeight);
      drawStroke(overlayCtx(), stroke);
      d.last = p;
    }
  };

  const onPointerUp = () => {
    const d = drawing.current;
    if (!d) return;
    drawing.current = null;
    overlayCtx().clearRect(0, 0, overlayRef.current!.clientWidth, overlayRef.current!.clientHeight);

    const { stroke } = d;
    if (stroke.kind !== 'freehand' && stroke.kind !== 'erase') {
      // Commit shape: draw onto the board canvas and send one op with [start, end].
      if (stroke.points.length < 2) return;
      drawStroke(boardCtx(), stroke);
    }
    opsRef.current = [...opsRef.current, stroke];
    socket.addStroke(stroke);
    (refreshHistory as any)._redo = false; // new op invalidates redo
    refreshHistory(users);
  };

  // --- Toolbar actions -----------------------------------------------------------
  const doClear = () => { if (window.confirm('Clear the canvas for everyone?')) socket.clear(); };
  const doExport = () => exportPNG(boardRef.current!);

  // Keyboard shortcuts — the ones every drawing app user expects.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === 'INPUT') return;
      const key = e.key.toLowerCase();
      if ((e.ctrlKey || e.metaKey) && key === 'z') { e.preventDefault(); e.shiftKey ? socket.redo() : socket.undo(); }
      else if ((e.ctrlKey || e.metaKey) && key === 'y') { e.preventDefault(); socket.redo(); }
      else if (key === 'p') setTool('pen');
      else if (key === 'e') setTool('eraser');
      else if (key === 'l') setTool('line');
      else if (key === 'r') setTool('rect');
      else if (key === 'c') setTool('circle');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [socket]);

  return (
    <div className="app">
      <div className="topbar">
        <span className="brand">Whiteboard</span>
        <span className="room-tag">room: {roomId}</span>
        <span className={`status ${status}`}>
          {status === 'online' ? 'connected' : status === 'offline' ? 'offline — reconnecting…' : 'connecting…'}
        </span>
        <div className="spacer" />
        <div className="users">
          {users.map(u => (
            <span key={u.id} className="user-chip">
              <span className="user-dot" style={{ background: u.color }} />{u.name}
            </span>
          ))}
        </div>
        <button className="action" onClick={onLeave}>Leave</button>
      </div>

      <Toolbar tool={tool} color={color} size={size}
        canUndo={history.undo} canRedo={history.redo}
        onTool={setTool} onColor={setColor} onSize={setSize}
        onUndo={() => socket.undo()} onRedo={() => socket.redo()}
        onClear={doClear} onExport={doExport} />

      <div ref={wrapRef} className="canvas-wrap">
        <canvas id="board" ref={boardRef}
          onPointerDown={onPointerDown} onPointerMove={onPointerMove}
          onPointerUp={onPointerUp} onPointerCancel={onPointerUp} />
        <canvas id="overlay" ref={overlayRef} />
      </div>
    </div>
  );
}

function socketIdOf(socket: BoardSocket): string {
  return socket.id;
}
