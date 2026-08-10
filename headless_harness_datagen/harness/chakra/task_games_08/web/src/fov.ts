// fov.ts
/**
 * Field‑of‑view calculation.
 * Returns a Set of "x,y" keys that are visible from the origin within a radius.
 * Simple line‑of‑sight using Bresenham; walls ('#') block sight.
 */
export function computeFOV(map: string[][], origin: [number, number], radius: number): Set<string> {
  const [ox, oy] = origin;
  const height = map.length;
  const width = map[0].length;
  const visible = new Set<string>();

  function isWall(x: number, y: number): boolean {
    return map[y][x] === '#';
  }

  // check all tiles within radius (square bounds) and test LOS
  for (let dy = -radius; dy <= radius; dy++) {
    for (let dx = -radius; dx <= radius; dx++) {
      const nx = ox + dx;
      const ny = oy + dy;
      if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
      if (dx * dx + dy * dy > radius * radius) continue;
      if (los(ox, oy, nx, ny, isWall)) {
        visible.add(`${nx},${ny}`);
      }
    }
  }
  return visible;
}

function los(x0: number, y0: number, x1: number, y1: number, blocker: (x:number,y:number)=>boolean): boolean {
  let dx = Math.abs(x1 - x0);
  let dy = Math.abs(y1 - y0);
  let x = x0;
  let y = y0;
  const n = 1 + dx + dy;
  const xInc = x1 > x0 ? 1 : -1;
  const yInc = y1 > y0 ? 1 : -1;
  let error = dx - dy;
  dx *= 2;
  dy *= 2;

  for (let i = 0; i < n; i++) {
    if (x !== x0 || y !== y0) {
      if (blocker(x, y)) return false;
    }
    if (x === x1 && y === y1) break;
    if (error > 0) {
      x += xInc;
      error -= dy;
    } else {
      y += yInc;
      error += dx;
    }
  }
  return true;
}
