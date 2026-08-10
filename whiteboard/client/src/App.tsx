import React, { useMemo, useState } from 'react';
import { Board } from './components/Board';
import { BoardSocket, type ConnStatus } from './socket';
import type { RoomState, Stroke, UserInfo } from './types';

// Join screen: room id + display name. Deep-linkable via ?room= so sharing a
// URL drops a teammate straight into the same board.
export default function App() {
  const [session, setSession] = useState<{ roomId: string; name: string } | null>(() => {
    const room = new URLSearchParams(location.search).get('room');
    const name = localStorage.getItem('wb_name');
    return room && name ? { roomId: room, name } : null;
  });
  const [name, setName] = useState(localStorage.getItem('wb_name') || '');
  const [room, setRoom] = useState(new URLSearchParams(location.search).get('room') || '');

  // Handlers are replaced by Board via setHandlers once mounted — the socket
  // instance itself is stable for the app's lifetime (survives re-renders).
  const socket = useMemo(() => new BoardSocket({
    onState: () => {}, onOpAdd: () => {}, onOpRemove: () => {}, onClear: () => {},
    onSegment: () => {}, onUserJoined: () => {}, onUserLeft: () => {}, onStatus: () => {}
  }), []);

  if (session) {
    return <Board socket={socket} roomId={session.roomId} name={session.name}
      onLeave={() => setSession(null)} />;
  }

  return (
    <form className="join-screen" onSubmit={e => {
      e.preventDefault();
      const r = room.trim() || 'lobby';
      localStorage.setItem('wb_name', name.trim());
      history.replaceState(null, '', `?room=${encodeURIComponent(r)}`);
      setSession({ roomId: r, name: name.trim() || 'anon' });
    }}>
      <h1>Join a whiteboard</h1>
      <input placeholder="Your name" value={name} required onChange={e => setName(e.target.value)} />
      <input placeholder="Room name (e.g. design-sync)" value={room} onChange={e => setRoom(e.target.value)} />
      <button type="submit">Join room</button>
    </form>
  );
}
