// Canvas renderer: board tiles, cover glyphs, core, units with HP bars and AP
// pips, movement highlights, attack preview. 960x720 canvas, 12x9 grid.

import type { GameState, Unit, Vec } from '../core/types';
import { BOARD_W, BOARD_H, tileAt, UNIT_STATS } from '../core/types';
import type { ShotPreview } from '../core/combat';

export const CELL = 72;
export const PAD = 48;
export const CANVAS_W = PAD * 2 + BOARD_W * CELL; // 960
export const CANVAS_H = PAD * 2 + BOARD_H * CELL; // 744

export interface RenderOptions {
  selected: Unit | null;
  moveHighlights: Map<string, number>;
  hoverTile: Vec | null;
  shotPreview: { target: Unit; preview: ShotPreview } | null;
  reachableTargets: Set<string>;
  paused: boolean;
}

export function tileFromPixel(px: number, py: number): Vec | null {
  const x = Math.floor((px - PAD) / CELL);
  const y = Math.floor((py - PAD) / CELL);
  if (x < 0 || y < 0 || x >= BOARD_W || y >= BOARD_H) return null;
  return { x, y };
}

const COLORS = {
  open: '#2a2118',
  openAlt: '#241d15',
  crate: '#7a5a33',
  container: '#4a5560',
  corespawn: '#3d2f52',
  player: '#d98e4a',
  playerDark: '#8a5527',
  ai: '#4aa3a2',
  aiDark: '#2a6564',
  grid: '#16110c',
  moveHi: 'rgba(120, 190, 255, 0.22)',
  targetHi: 'rgba(217, 95, 74, 0.35)',
  core: '#ffd76a',
};

export function render(ctx: CanvasRenderingContext2D, state: GameState, opts: RenderOptions): void {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  // Tiles.
  for (let y = 0; y < BOARD_H; y++) {
    for (let x = 0; x < BOARD_W; x++) {
      const px = PAD + x * CELL;
      const py = PAD + y * CELL;
      const t = tileAt(state.board, x, y);
      ctx.fillStyle = (x + y) % 2 === 0 ? COLORS.open : COLORS.openAlt;
      ctx.fillRect(px, py, CELL, CELL);
      if (t === 'crate') {
        ctx.fillStyle = COLORS.crate;
        ctx.fillRect(px + 10, py + 10, CELL - 20, CELL - 20);
        ctx.strokeStyle = '#3d2c17';
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 10, py + 10, CELL - 20, CELL - 20);
        ctx.beginPath();
        ctx.moveTo(px + 10, py + 10);
        ctx.lineTo(px + CELL - 10, py + CELL - 10);
        ctx.moveTo(px + CELL - 10, py + 10);
        ctx.lineTo(px + 10, py + CELL - 10);
        ctx.stroke();
        ctx.fillStyle = '#2c2012';
        ctx.font = '9px monospace';
        ctx.fillText('CRATE', px + 18, py + CELL - 14);
      } else if (t === 'container') {
        ctx.fillStyle = COLORS.container;
        ctx.fillRect(px + 4, py + 4, CELL - 8, CELL - 8);
        ctx.strokeStyle = '#222a30';
        ctx.lineWidth = 3;
        ctx.strokeRect(px + 4, py + 4, CELL - 8, CELL - 8);
        ctx.strokeStyle = '#5d6b78';
        ctx.lineWidth = 1;
        for (let i = 1; i < 4; i++) {
          ctx.beginPath();
          ctx.moveTo(px + 4 + (i * (CELL - 8)) / 4, py + 4);
          ctx.lineTo(px + 4 + (i * (CELL - 8)) / 4, py + CELL - 4);
          ctx.stroke();
        }
        ctx.fillStyle = '#10151a';
        ctx.font = '9px monospace';
        ctx.fillText('CONTAINER', px + 8, py + CELL - 8);
      } else if (t === 'corespawn') {
        ctx.fillStyle = COLORS.corespawn;
        ctx.fillRect(px + 6, py + 6, CELL - 12, CELL - 12);
        ctx.fillStyle = '#7a68a8';
        ctx.font = '9px monospace';
        ctx.fillText('CORE PAD', px + 14, py + CELL - 10);
      }
      ctx.strokeStyle = COLORS.grid;
      ctx.lineWidth = 1;
      ctx.strokeRect(px, py, CELL, CELL);
    }
  }

  // Extraction rows.
  for (const team of ['player', 'ai'] as const) {
    const row = state.board.extractionRow[team];
    ctx.fillStyle = team === 'player' ? 'rgba(217,142,74,0.16)' : 'rgba(74,163,162,0.16)';
    ctx.fillRect(PAD, PAD + row * CELL, BOARD_W * CELL, CELL);
    ctx.fillStyle = team === 'player' ? COLORS.player : COLORS.ai;
    ctx.font = 'bold 10px monospace';
    ctx.fillText(
      team === 'player' ? 'COPPERJACK EXTRACTION' : 'FERROSCOUT EXTRACTION',
      PAD + 6,
      PAD + row * CELL + 12,
    );
  }

  // Movement highlights.
  for (const key of opts.moveHighlights.keys()) {
    const [x, y] = key.split(',').map(Number);
    ctx.fillStyle = COLORS.moveHi;
    ctx.fillRect(PAD + x * CELL + 1, PAD + y * CELL + 1, CELL - 2, CELL - 2);
  }

  // Reachable attack targets highlight.
  for (const id of opts.reachableTargets) {
    const u = state.units.find((u) => u.id === id);
    if (!u) continue;
    ctx.fillStyle = COLORS.targetHi;
    ctx.fillRect(PAD + u.pos.x * CELL + 1, PAD + u.pos.y * CELL + 1, CELL - 2, CELL - 2);
  }

  // Hover tile.
  if (opts.hoverTile) {
    ctx.strokeStyle = '#e8dcc8';
    ctx.lineWidth = 2;
    ctx.strokeRect(PAD + opts.hoverTile.x * CELL + 1, PAD + opts.hoverTile.y * CELL + 1, CELL - 2, CELL - 2);
  }

  // Core (when on the ground).
  if (state.core.pos) {
    const { x, y } = state.core.pos;
    const cx = PAD + x * CELL + CELL / 2;
    const cy = PAD + y * CELL + CELL / 2;
    ctx.fillStyle = COLORS.core;
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 3) * i - Math.PI / 6;
      const r = 13;
      const vx = cx + r * Math.cos(a);
      const vy = cy + r * Math.sin(a);
      if (i === 0) ctx.moveTo(vx, vy);
      else ctx.lineTo(vx, vy);
    }
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = '#8a6a1a';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#3d2f08';
    ctx.font = 'bold 9px monospace';
    ctx.fillText('CORE', cx - 12, cy + 3);
  }

  // Units.
  for (const u of state.units) {
    if (!u.alive) continue;
    const cx = PAD + u.pos.x * CELL + CELL / 2;
    const cy = PAD + u.pos.y * CELL + CELL / 2;
    const base = u.team === 'player' ? COLORS.player : COLORS.ai;
    const dark = u.team === 'player' ? COLORS.playerDark : COLORS.aiDark;

    ctx.fillStyle = base;
    ctx.strokeStyle = dark;
    ctx.lineWidth = 3;
    ctx.beginPath();
    if (u.cls === 'bruiser') {
      // Square bruiser.
      ctx.rect(cx - 18, cy - 18, 36, 36);
    } else if (u.cls === 'runner') {
      // Triangle runner.
      ctx.moveTo(cx, cy - 20);
      ctx.lineTo(cx + 18, cy + 14);
      ctx.lineTo(cx - 18, cy + 14);
      ctx.closePath();
    } else {
      // Circle spotter.
      ctx.arc(cx, cy, 18, 0, Math.PI * 2);
    }
    ctx.fill();
    ctx.stroke();

    // Class glyph + selection ring.
    ctx.fillStyle = '#14100d';
    ctx.font = 'bold 14px monospace';
    const glyph = u.cls === 'bruiser' ? 'B' : u.cls === 'runner' ? 'R' : 'S';
    ctx.fillText(glyph, cx - 5, cy + 5);

    if (opts.selected?.id === u.id) {
      ctx.strokeStyle = '#ffe9b0';
      ctx.lineWidth = 2;
      ctx.strokeRect(PAD + u.pos.x * CELL + 3, PAD + u.pos.y * CELL + 3, CELL - 6, CELL - 6);
    }

    // HP bar.
    const bw = 44;
    const bx = cx - bw / 2;
    const by = cy + 24;
    ctx.fillStyle = '#000';
    ctx.fillRect(bx, by, bw, 6);
    const frac = u.hp / u.maxHp;
    ctx.fillStyle = frac > 0.5 ? '#6ab04c' : frac > 0.25 ? '#e0a83c' : '#d95f4a';
    ctx.fillRect(bx, by, bw * frac, 6);
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx, by, bw, 6);

    // AP pips (only on the active team's turn).
    if (u.team === state.active && !state.over) {
      for (let i = 0; i < 2; i++) {
        ctx.fillStyle = i < u.ap ? '#ffe9b0' : '#3a2f22';
        ctx.beginPath();
        ctx.arc(cx - 8 + i * 16, by + 14, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Core marker on the carrier.
    if (u.hasCore) {
      ctx.fillStyle = COLORS.core;
      ctx.beginPath();
      ctx.arc(cx + 16, cy - 16, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#8a6a1a';
      ctx.stroke();
    }
  }

  // Attack preview: line + hit % tag.
  if (opts.shotPreview && opts.selected) {
    const { target, preview } = opts.shotPreview;
    const ax = PAD + opts.selected.pos.x * CELL + CELL / 2;
    const ay = PAD + opts.selected.pos.y * CELL + CELL / 2;
    const tx = PAD + target.pos.x * CELL + CELL / 2;
    const ty = PAD + target.pos.y * CELL + CELL / 2;
    ctx.strokeStyle = preview.canShoot ? '#ffd76a' : '#d95f4a';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(ax, ay);
    ctx.lineTo(tx, ty);
    ctx.stroke();
    ctx.setLineDash([]);
    const label = preview.canShoot
      ? `${Math.round(preview.chance * 100)}% ${preview.halfCover ? '(cover)' : ''} dmg ${preview.dmg}`
      : preview.reason ?? 'No shot';
    ctx.font = 'bold 13px monospace';
    const tw = ctx.measureText(label).width;
    ctx.fillStyle = 'rgba(0,0,0,0.75)';
    ctx.fillRect(tx - tw / 2 - 6, ty - 34, tw + 12, 18);
    ctx.fillStyle = preview.canShoot ? '#ffd76a' : '#d95f4a';
    ctx.fillText(label, tx - tw / 2, ty - 21);
  }

  // Pause veil.
  if (opts.paused) {
    ctx.fillStyle = 'rgba(10,7,5,0.7)';
    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.fillStyle = '#e8dcc8';
    ctx.font = 'bold 30px monospace';
    ctx.fillText('PAUSED — press P', ctx.canvas.width / 2 - 150, ctx.canvas.height / 2);
  }
}
