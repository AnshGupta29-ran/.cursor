// Three hand-authored junkyard layouts.
// Legend: '.' open, 'c' crate (half cover), '#' container (full cover), 'X' core spawn.
// Player (Copperjacks) extracts on the bottom row (y = 8).
// AI (Ferroscouts) extracts on the top row (y = 0).

import { BOARD_H, BOARD_W, MapDef } from '../core/types.js';

export const MAPS: MapDef[] = [
  {
    id: 'scrapyard-cross',
    name: 'Scrapyard Cross',
    rows: [
      '............',
      '.c........c.',
      '.....##.....',
      '..c......c..',
      '...c.XX.c...',
      '..c......c..',
      '.....##.....',
      '.c........c.',
      '............',
    ],
    spawns: {
      player: [
        { cls: 'bruiser', x: 4, y: 7 },
        { cls: 'runner', x: 6, y: 8 },
        { cls: 'spotter', x: 8, y: 7 },
      ],
      ai: [
        { cls: 'bruiser', x: 7, y: 1 },
        { cls: 'runner', x: 5, y: 0 },
        { cls: 'spotter', x: 3, y: 1 },
      ],
    },
  },
  {
    id: 'container-alley',
    name: 'Container Alley',
    rows: [
      '............',
      '....#..#....',
      '.c..#..#..c.',
      '.c........c.',
      '....cXXc....',
      '.c........c.',
      '.c..#..#..c.',
      '....#..#....',
      '............',
    ],
    spawns: {
      player: [
        { cls: 'bruiser', x: 3, y: 8 },
        { cls: 'runner', x: 6, y: 7 },
        { cls: 'spotter', x: 9, y: 8 },
      ],
      ai: [
        { cls: 'bruiser', x: 8, y: 0 },
        { cls: 'runner', x: 5, y: 1 },
        { cls: 'spotter', x: 2, y: 0 },
      ],
    },
  },
  {
    id: 'husk-field',
    name: 'Husk Field',
    rows: [
      '............',
      '..c..##..c..',
      '............',
      '.##......##.',
      '.....XX.....',
      '.##......##.',
      '............',
      '..c..##..c..',
      '............',
    ],
    spawns: {
      player: [
        { cls: 'bruiser', x: 5, y: 8 },
        { cls: 'runner', x: 6, y: 7 },
        { cls: 'spotter', x: 6, y: 8 },
      ],
      ai: [
        { cls: 'bruiser', x: 6, y: 0 },
        { cls: 'runner', x: 5, y: 1 },
        { cls: 'spotter', x: 5, y: 0 },
      ],
    },
  },
];

export function getMap(id: string): MapDef {
  const m = MAPS.find((m) => m.id === id);
  if (!m) throw new Error(`Unknown map: ${id}`);
  for (const row of m.rows) {
    if (row.length !== BOARD_W) throw new Error(`Map ${id} row width mismatch`);
  }
  if (m.rows.length !== BOARD_H) throw new Error(`Map ${id} height mismatch`);
  return m;
}
