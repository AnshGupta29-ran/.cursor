import type { Point, Stroke, StrokeStyle } from '../types';

// Canvas rendering lives outside React entirely. Reasoning: React re-renders
// are the wrong granularity for pointermove events (60+/sec). The Board
// component owns refs and calls these functions directly; React only owns
// toolbars and presence UI.
//
// Coordinate model: all points are stored in CSS pixels. The canvas backing
// store is scaled by devicePixelRatio (and ctx.setTransform(dpr,...)), so
// rendering is sharp on retina with zero bookkeeping in draw code.

export function drawStroke(ctx: CanvasRenderingContext2D, stroke: Stroke): void {
  const pts = stroke.points;
  if (!pts.length) return;

  ctx.save();
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.lineWidth = stroke.style.size;

  if (stroke.kind === 'erase') {
    // Eraser = destination-out painting. On the white base this reads as
    // "white paint", but compositing keeps it correct over any background.
    ctx.globalCompositeOperation = 'destination-out';
    ctx.strokeStyle = 'rgba(0,0,0,1)';
    strokePath(ctx, pts);
  } else if (stroke.kind === 'freehand') {
    ctx.strokeStyle = stroke.style.color;
    strokePath(ctx, pts);
  } else {
    ctx.strokeStyle = stroke.style.color;
    const [a, b] = [pts[0], pts[pts.length - 1]];
    if (stroke.kind === 'rect') {
      ctx.strokeRect(a.x, a.y, b.x - a.x, b.y - a.y);
    } else if (stroke.kind === 'line') {
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    } else { // circle = ellipse inscribed in the drag box
      ctx.beginPath();
      ctx.ellipse((a.x + b.x) / 2, (a.y + b.y) / 2,
        Math.abs(b.x - a.x) / 2, Math.abs(b.y - a.y) / 2, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function strokePath(ctx: CanvasRenderingContext2D, pts: Point[]): void {
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  if (pts.length === 1) {
    // A dot: lineTo the same point renders nothing, so draw a tiny segment.
    ctx.lineTo(pts[0].x + 0.01, pts[0].y + 0.01);
  } else {
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  }
  ctx.stroke();
}

// Incremental segment for live drawing (own pointer + remote segments):
// avoids a full redraw per pointermove.
export function drawSegment(
  ctx: CanvasRenderingContext2D, kind: string, style: StrokeStyle, a: Point, b: Point
): void {
  ctx.save();
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.lineWidth = style.size;
  if (kind === 'erase') {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.strokeStyle = 'rgba(0,0,0,1)';
  } else {
    ctx.strokeStyle = style.color;
  }
  ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
  ctx.restore();
}

// Full replay from the op log — used on join, reconnect, undo, redo, clear.
export function redrawAll(ctx: CanvasRenderingContext2D, ops: Stroke[], w: number, h: number): void {
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0); // reset to device pixels for a full clear
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.restore();
  for (const op of ops) drawStroke(ctx, op);
}

// Export composes onto a white background first — PNG transparency would
// otherwise render the board as black in many viewers.
export function exportPNG(canvas: HTMLCanvasElement): void {
  const out = document.createElement('canvas');
  out.width = canvas.width;
  out.height = canvas.height;
  const ctx = out.getContext('2d')!;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, out.width, out.height);
  ctx.drawImage(canvas, 0, 0);
  const a = document.createElement('a');
  a.download = `whiteboard-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.png`;
  a.href = out.toDataURL('image/png');
  a.click();
}
