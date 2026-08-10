import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Bucket, ViewId, Workspace, ResumeAsset } from './types';
import { scoreResume, suggestedBucket, THRESHOLD_PRESETS, validateResumeText } from './engine';
import {
  loadWorkspace,
  saveWorkspace,
  audit,
  exportWorkspaceJson,
  exportDecisionsCsv,
  importWorkspaceJson,
} from './storage';
import './styles.css';
// Removed unused component imports

function uid(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
}

function HighlightedText({ text, spans }: { text: string; spans: { start: number; end: number }[] }) {
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  sorted.forEach((s, i) => {
    if (s.start > cursor) nodes.push(text.slice(cursor, s.start));
    nodes.push(<mark key={i}>{text.slice(s.start, s.end)}</mark>);
    cursor = s.end;
  });
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return <div className="evidence">{nodes}</div>;
}

export default function App() {
  const [ws, setWs] = useState<Workspace>(() => loadWorkspace());
  const [view, setView] = useState<ViewId>('queue');
  const [sel, setSel] = useState(0);
  const [announce, setAnnounce] = useState('');
  const [helpOpen, setHelpOpen] = useState(false);
  const [storageErr, setStorageErr] = useState<string | null>(null);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const helpReturnFocus = useRef<HTMLElement | null>(null);
  const helpCloseBtn = useRef<HTMLButtonElement | null>(null);

  const profile = ws.profiles.find((p) => p.id === ws.activeProfileId) ?? ws.profiles[0];

  const persist = useCallback((next: Workspace, live?: string) => {
    setWs(next);
    const err = saveWorkspace(next);
    setStorageErr(err);
    if (live) setAnnounce(live);
  }, []);

  const rescoreAll = useCallback(
    (next: Workspace) => {
      const p = next.profiles.find((x) => x.id === next.activeProfileId) ?? next.profiles[0];
      next.results = next.resumes.filter((r) => r.status === 'valid').map((r) => scoreResume(r, p));
      next.decisions = next.results.map((res) => {
        const prev = next.decisions.find((d) => d.resumeId === res.resumeId);
        if (prev?.confirmed) return prev;
        return {
          resumeId: res.resumeId,
          bucket: suggestedBucket(res.totalScore, p.thresholds),
          decidedBy: 'system-suggest',
          timestamp: new Date().toISOString(),
          confirmed: false,
          note: 'auto-bucketed; human must confirm',
        };
      });
      return next;
    },
    []
  );

  const selectedResume = ws.resumes[sel];
  const selectedResult = selectedResume
    ? ws.results.find((r) => r.resumeId === selectedResume.id)
    : undefined;
  const selectedDecision = selectedResume
    ? ws.decisions.find((d) => d.resumeId === selectedResume.id)
    : undefined;

  const setBucket = useCallback(
    (bucket: Bucket) => {
      if (!selectedResume) return;
      const next = structuredClone(ws);
      const idx = next.decisions.findIndex((d) => d.resumeId === selectedResume.id);
      const row = {
        resumeId: selectedResume.id,
        bucket,
        decidedBy: 'reviewer',
        timestamp: new Date().toISOString(),
        confirmed: true,
      };
      if (idx >= 0) next.decisions[idx] = row;
      else next.decisions.push(row);
      audit(next, 'decision', { resumeId: selectedResume.id, bucket, filename: selectedResume.filename });
      persist(next, `Candidate ${selectedResume.filename} moved to ${bucket}`);
    },
    [persist, selectedResume, ws]
  );

  const doExport = useCallback(
    (kind: 'json' | 'csv' | 'workspace') => {
      const blob =
        kind === 'csv'
          ? new Blob([exportDecisionsCsv(ws)], { type: 'text/csv' })
          : kind === 'workspace'
            ? new Blob([exportWorkspaceJson(ws)], { type: 'application/json' })
            : new Blob(
                [
                  JSON.stringify(
                    { decisions: ws.decisions, audit: ws.audit, results: ws.results },
                    null,
                    2
                  ),
                ],
                { type: 'application/json' }
              );
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download =
        kind === 'csv' ? 'meritlens-decisions.csv' : kind === 'workspace' ? 'meritlens-workspace.json' : 'meritlens-export.json';
      a.click();
      URL.revokeObjectURL(a.href);
      const next = structuredClone(ws);
      audit(next, 'export', { kind });
      persist(next, `Exported ${kind}`);
    },
    [persist, ws]
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;

      if (helpOpen) {
        if (e.key === 'Escape') {
          e.preventDefault();
          setHelpOpen(false);
          helpReturnFocus.current?.focus();
        }
        return;
      }

      if (e.key === '?') {
        e.preventDefault();
        helpReturnFocus.current = document.activeElement as HTMLElement;
        setHelpOpen(true);
        return;
      }
      if (e.key === '1') {
        setView('queue');
        return;
      }
      if (e.key === '2') {
        setView('detail');
        return;
      }
      if (e.key === '3') {
        setView('roles');
        return;
      }
      if (view === 'queue' || view === 'detail') {
        if (e.key === 'j' || e.key === 'ArrowDown') {
          e.preventDefault();
          setSel((s) => Math.min(s + 1, Math.max(0, ws.resumes.length - 1)));
        } else if (e.key === 'k' || e.key === 'ArrowUp') {
          e.preventDefault();
          setSel((s) => Math.max(0, s - 1));
        } else if (e.key === 'Enter' && view === 'queue') {
          e.preventDefault();
          setView('detail');
        } else if (e.key === 'a') {
          e.preventDefault();
          setBucket('advance');
        } else if (e.key === 'h') {
          e.preventDefault();
          setBucket('hold');
        } else if (e.key === 'r') {
          e.preventDefault();
          setBucket('reject');
        } else if (e.key === 'e') {
          e.preventDefault();
          doExport('json');
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [doExport, helpOpen, setBucket, view, ws.resumes.length]);

  useEffect(() => {
    if (helpOpen) helpCloseBtn.current?.focus();
  }, [helpOpen]);

  const allSpans = useMemo(() => {
    if (!selectedResult) return [];
    return selectedResult.breakdown.flatMap((b) => b.evidenceSpans);
  }, [selectedResult]);

  async function onFiles(fileList: FileList | null) {
    if (!fileList?.length) return;
    const next = structuredClone(ws);
    const messages: string[] = [];
    for (const file of Array.from(fileList)) {
      const text = await file.text();
      const check = validateResumeText(file.name, text);
      if (!check.ok) {
        messages.push(check.reason);
        audit(next, 'import_reject', { filename: file.name, reason: check.reason });
        continue;
      }
      if (next.resumes.some((r) => r.filename === file.name)) {
        messages.push(`Duplicate filename flagged: "${file.name}"`);
      }
      const asset: ResumeAsset = {
        id: uid('res'),
        filename: file.name,
        rawText: text,
        importedAt: new Date().toISOString(),
        status: 'valid',
      };
      next.resumes.push(asset);
      audit(next, 'import', { filename: file.name, id: asset.id });
    }
    rescoreAll(next);
    persist(next, `Imported files; ${messages.length ? messages.join(' ') : 'ok'}`);
    setImportMsg(messages.length ? messages.join(' | ') : 'Import OK');
  }

  function onPasteImport(raw: string, filename = 'pasted.txt') {
    const check = validateResumeText(filename, raw);
    if (!check.ok) {
      setImportMsg(check.reason);
      return;
    }
    const next = structuredClone(ws);
    if (next.resumes.some((r) => r.filename === filename)) {
      setImportMsg(`Duplicate filename flagged: "${filename}"`);
    }
    next.resumes.push({
      id: uid('res'),
      filename,
      rawText: raw,
      importedAt: new Date().toISOString(),
      status: 'valid',
    });
    audit(next, 'import_paste', { filename });
    rescoreAll(next);
    persist(next, `Pasted resume ${filename}`);
    setImportMsg('Paste import OK');
  }

  function updateThresholds(advance: number, hold: number, preset?: string) {
    const next = structuredClone(ws);
    const p = next.profiles.find((x) => x.id === next.activeProfileId)!;
    p.thresholds = { advance, hold };
    audit(next, 'threshold_edit', { advance, hold, preset: preset ?? 'custom' });
    rescoreAll(next);
    persist(next, `Thresholds updated${preset ? ` (${preset})` : ''}; queue re-bucketed`);
  }

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main
      </a>
      <div className="live" aria-live="polite">
        {announce}
      </div>
      <header className="app-header">
        <h1>MeritLens</h1>
        <span className="tag">Auditable apprenticeship cohort screening — not a black-box match %</span>
      </header>
      <nav className="tabs" aria-label="Primary">
        <button type="button" aria-selected={view === 'queue'} onClick={() => setView('queue')}>
          Queue (1)
        </button>
        <button type="button" aria-selected={view === 'detail'} onClick={() => setView('detail')}>
          Candidate (2)
        </button>
        <button type="button" aria-selected={view === 'roles'} onClick={() => setView('roles')}>
          Roles & Thresholds (3)
        </button>
      </nav>
      <main id="main">
        {storageErr && <p className="err">{storageErr}</p>}
        {importMsg && <p className="muted">{importMsg}</p>}

        {view === 'queue' && (
          <section aria-labelledby="queue-h">
            <h2 id="queue-h">Review queue — {profile?.name}</h2>
            <p className="muted">
              j/k select · Enter detail · a/h/r bucket · e export · ? help. Suggestions are not final until you confirm.
            </p>
            <div className="toolbar">
              <label className="action">
                Upload .txt/.md
                <input
                  type="file"
                  accept=".txt,.md,text/plain"
                  multiple
                  hidden
                  onChange={(e) => onFiles(e.target.files)}
                />
              </label>
              <button type="button" className="action" onClick={() => doExport('json')}>
                Export JSON
              </button>
              <button type="button" className="action" onClick={() => doExport('csv')}>
                Export CSV
              </button>
              <button type="button" className="action" onClick={() => doExport('workspace')}>
                Export workspace
              </button>
            </div>
            <ul className="queue-list panel" role="listbox" aria-label="Candidates">
              <li className="muted" aria-hidden="true" style={{ cursor: 'default' }}>
                <span>Candidate</span>
                <span>Score</span>
                <span>Bucket</span>
                <span>Confirmed</span>
              </li>
              {ws.resumes.map((r, i) => {
                const res = ws.results.find((x) => x.resumeId === r.id);
                const dec = ws.decisions.find((x) => x.resumeId === r.id);
                const bucket = dec?.bucket ?? 'reject';
                return (
                  <li
                    key={r.id}
                    role="option"
                    tabIndex={i === sel ? 0 : -1}
                    aria-selected={i === sel}
                    onClick={() => {
                      setSel(i);
                      setView('detail');
                    }}
                    onFocus={() => setSel(i)}
                  >
                    <span>{r.filename}</span>
                    <span>{res ? res.totalScore.toFixed(1) : '—'}</span>
                    <span className={`bucket-${bucket}`}>{bucket}</span>
                    <span>{dec?.confirmed ? 'yes' : 'pending'}</span>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {view === 'detail' && selectedResume && (
          <section aria-labelledby="detail-h">
            <h2 id="detail-h">{selectedResume.filename}</h2>
            <div className="toolbar">
              <button type="button" className="action" onClick={() => setBucket('advance')}>
                Advance (a)
              </button>
              <button type="button" className="action" onClick={() => setBucket('hold')}>
                Hold (h)
              </button>
              <button type="button" className="action" onClick={() => setBucket('reject')}>
                Reject (r)
              </button>
              <button type="button" className="action" onClick={() => setView('queue')}>
                Back to queue
              </button>
            </div>
            <div className="layout-split">
              <div className="panel">
                <h3>Rubric decomposition</h3>
                {selectedResult ? (
                  <>
                    <p>
                      <strong>{selectedResult.totalScore.toFixed(1)}</strong> / 100 · confidence{' '}
                      {(selectedResult.confidence * 100).toFixed(0)}% · suggested{' '}
                      <span className={`bucket-${selectedDecision?.bucket}`}>
                        {selectedDecision?.bucket}
                      </span>
                      {selectedDecision?.confirmed ? ' (confirmed)' : ' (unconfirmed)'}
                    </p>
                    {selectedResult.explanation && <p className="muted">{selectedResult.explanation}</p>}
                    <table className="breakdown">
                      <thead>
                        <tr>
                          <th>Criterion</th>
                          <th>Match</th>
                          <th>Points</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedResult.breakdown.map((b) => (
                          <tr key={b.criterion}>
                            <td>{b.criterion}</td>
                            <td>{b.matched ? 'yes' : 'missing'}</td>
                            <td>{b.points}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="muted">
                      Matched: {selectedResult.matchedSkills.join(', ') || 'none'}. Missing:{' '}
                      {selectedResult.missingSkills.join(', ') || 'none'}.
                    </p>
                  </>
                ) : (
                  <p className="err">No score</p>
                )}
              </div>
              <div className="panel">
                <h3>Evidence in resume</h3>
                <HighlightedText text={selectedResume.rawText} spans={allSpans} />
                <h3>vs job description</h3>
                <div className="evidence">{profile?.jobDescription ?? ''}</div>
              </div>
            </div>
          </section>
        )}

        {view === 'roles' && profile && (
          <section aria-labelledby="roles-h">
            <h2 id="roles-h">Roles & thresholds</h2>
            <div className="panel">
              <p>
                Active role: <strong>{profile.name}</strong>
              </p>
              <label>
                Job description
                <textarea
                  rows={4}
                  value={profile.jobDescription ?? ''}
                  onChange={(e) => {
                    const next = structuredClone(ws);
                    const p = next.profiles.find((x) => x.id === profile.id)!;
                    p.jobDescription = e.target.value;
                    persist(next);
                  }}
                />
              </label>
              <p>
                Advance ≥ {profile.thresholds.advance} · Hold ≥ {profile.thresholds.hold} (else reject)
              </p>
              <div className="toolbar">
                <button
                  type="button"
                  className="action"
                  onClick={() =>
                    updateThresholds(THRESHOLD_PRESETS.strict.advance, THRESHOLD_PRESETS.strict.hold, 'strict')
                  }
                >
                  Preset: strict
                </button>
                <button
                  type="button"
                  className="action"
                  onClick={() =>
                    updateThresholds(
                      THRESHOLD_PRESETS['open-cohort'].advance,
                      THRESHOLD_PRESETS['open-cohort'].hold,
                      'open-cohort'
                    )
                  }
                >
                  Preset: open-cohort
                </button>
              </div>
              <div className="layout-split">
                <label>
                  Advance threshold
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={profile.thresholds.advance}
                    onChange={(e) =>
                      updateThresholds(Number(e.target.value), profile.thresholds.hold)
                    }
                  />
                </label>
                <label>
                  Hold threshold
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={profile.thresholds.hold}
                    onChange={(e) =>
                      updateThresholds(profile.thresholds.advance, Number(e.target.value))
                    }
                  />
                </label>
              </div>
              <h3>Criteria</h3>
              <ul>
                {profile.criteria.map((c) => (
                  <li key={c.skill}>
                    {c.skill} (w={c.weight})
                    {c.synonyms.length ? ` — synonyms: ${c.synonyms.join(', ')}` : ''}
                  </li>
                ))}
              </ul>
              <h3>Paste resume text</h3>
              <PasteBox onImport={onPasteImport} />
              <h3>Import workspace JSON</h3>
              <label className="action">
                Choose file
                <input
                  type="file"
                  accept="application/json,.json"
                  hidden
                  onChange={async (e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    const text = await f.text();
                    const parsed = importWorkspaceJson(text);
                    if ('error' in parsed) {
                      setImportMsg(parsed.error);
                      return;
                    }
                    persist(parsed, 'Workspace imported');
                    setImportMsg('Workspace imported');
                  }}
                />
              </label>
            </div>
          </section>
        )}
      </main>

      {helpOpen && (
        <div className="overlay" role="presentation">
          <div
            className="overlay-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
            onKeyDown={(e) => {
              if (e.key === 'Tab') {
                const focusables = [helpCloseBtn.current].filter(Boolean) as HTMLElement[];
                if (!focusables.length) return;
                e.preventDefault();
                focusables[0].focus();
              }
            }}
          >
            <h2 id="help-title">Keyboard shortcuts</h2>
            <ul>
              <li>
                <kbd>j</kbd>/<kbd>k</kbd> or arrows — move queue selection
              </li>
              <li>
                <kbd>Enter</kbd> — open candidate detail
              </li>
              <li>
                <kbd>a</kbd>/<kbd>h</kbd>/<kbd>r</kbd> — advance / hold / reject
              </li>
              <li>
                <kbd>e</kbd> — export decisions JSON
              </li>
              <li>
                <kbd>1</kbd>/<kbd>2</kbd>/<kbd>3</kbd> — Queue / Detail / Roles
              </li>
              <li>
                <kbd>?</kbd> help · <kbd>Esc</kbd> close
              </li>
            </ul>
            <button
              ref={helpCloseBtn}
              type="button"
              className="action"
              onClick={() => {
                setHelpOpen(false);
                helpReturnFocus.current?.focus();
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function PasteBox({ onImport }: { onImport: (text: string, filename?: string) => void }) {
  const [text, setText] = useState('');
  const [name, setName] = useState('pasted.txt');
  return (
    <div>
      <label>
        Filename
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label>
        Body
        <textarea rows={5} value={text} onChange={(e) => setText(e.target.value)} />
      </label>
      <button
        type="button"
        className="action"
        onClick={() => {
          onImport(text, name);
          setText('');
        }}
      >
        Import paste
      </button>
    </div>
  );
}
