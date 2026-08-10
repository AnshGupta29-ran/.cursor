import React from 'react';
import type { Tool } from '../types';

const TOOLS: { id: Tool; label: string; title: string }[] = [
  { id: 'pen', label: '✏️ Pen', title: 'Freehand (P)' },
  { id: 'eraser', label: '🧹 Eraser', title: 'Erase (E)' },
  { id: 'line', label: '╱ Line', title: 'Line (L)' },
  { id: 'rect', label: '▭ Rect', title: 'Rectangle (R)' },
  { id: 'circle', label: '◯ Circle', title: 'Circle (C)' }
];

interface Props {
  tool: Tool;
  color: string;
  size: number;
  canUndo: boolean;
  canRedo: boolean;
  onTool: (t: Tool) => void;
  onColor: (c: string) => void;
  onSize: (s: number) => void;
  onUndo: () => void;
  onRedo: () => void;
  onClear: () => void;
  onExport: () => void;
}

export function Toolbar(p: Props) {
  return (
    <div className="toolbar">
      <div className="group" role="toolbar" aria-label="tools">
        {TOOLS.map(t => (
          <button key={t.id} title={t.title}
            className={'tool' + (p.tool === t.id ? ' active' : '')}
            onClick={() => p.onTool(t.id)}>
            {t.label}
          </button>
        ))}
      </div>
      <div className="group">
        <input type="color" value={p.color} title="Brush color"
          onChange={e => p.onColor(e.target.value)} />
        <input type="range" min={1} max={40} value={p.size} title="Brush size"
          onChange={e => p.onSize(Number(e.target.value))} />
        <span className="size-label">{p.size}px</span>
      </div>
      <div className="group">
        <button className="action" disabled={!p.canUndo} title="Undo (Ctrl+Z)" onClick={p.onUndo}>↩ Undo</button>
        <button className="action" disabled={!p.canRedo} title="Redo (Ctrl+Y)" onClick={p.onRedo}>↪ Redo</button>
        <button className="action danger" title="Clear canvas for everyone" onClick={p.onClear}>Clear</button>
      </div>
      <div className="group">
        <button className="action" title="Export as PNG" onClick={p.onExport}>⬇ Export PNG</button>
      </div>
    </div>
  );
}
