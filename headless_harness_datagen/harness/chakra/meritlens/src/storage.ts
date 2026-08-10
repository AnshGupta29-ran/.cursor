import type { Workspace, AuditEvent } from './types';
import { createSeedWorkspace } from './seed';

const KEY = 'meritlens.v1';

export function loadWorkspace(): Workspace {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return createSeedWorkspace();
    const parsed = JSON.parse(raw) as Workspace;
    if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.profiles)) {
      console.warn('MeritLens: corrupt workspace — resetting to seed');
      const seed = createSeedWorkspace();
      saveWorkspace(seed);
      return seed;
    }
    return parsed;
  } catch {
    console.warn('MeritLens: failed to parse workspace — resetting');
    const seed = createSeedWorkspace();
    try {
      saveWorkspace(seed);
    } catch {
      /* quota */
    }
    return seed;
  }
}

export function saveWorkspace(ws: Workspace): string | null {
  try {
    localStorage.setItem(KEY, JSON.stringify(ws));
    return null;
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'localStorage write failed';
    return `Storage error (quota?): ${msg}`;
  }
}

export function audit(ws: Workspace, type: string, payload: Record<string, unknown>): AuditEvent {
  const ev: AuditEvent = { type, payload, timestamp: new Date().toISOString() };
  ws.audit.push(ev);
  return ev;
}

export function exportWorkspaceJson(ws: Workspace): string {
  return JSON.stringify(ws, null, 2);
}

export function exportDecisionsCsv(ws: Workspace): string {
  const header = 'resumeId,filename,bucket,score,confirmed,decidedBy,timestamp,note';
  const rows = ws.decisions.map((d) => {
    const resume = ws.resumes.find((r) => r.id === d.resumeId);
    const result = ws.results.find((r) => r.resumeId === d.resumeId);
    const cells = [
      d.resumeId,
      resume?.filename ?? '',
      d.bucket,
      result?.totalScore ?? '',
      d.confirmed,
      d.decidedBy,
      d.timestamp,
      (d.note ?? '').replace(/,/g, ';'),
    ];
    return cells.join(',');
  });
  return [header, ...rows].join('\n');
}

export function importWorkspaceJson(text: string): Workspace | { error: string } {
  try {
    const parsed = JSON.parse(text) as Workspace;
    if (!parsed || parsed.version !== 1) return { error: 'Invalid workspace JSON (need version:1)' };
    return parsed;
  } catch {
    return { error: 'Could not parse workspace JSON' };
  }
}
