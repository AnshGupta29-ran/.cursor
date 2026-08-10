import { describe, it, expect } from 'vitest';
import { scoreResume, validateResumeText, suggestedBucket } from '../src/engine';
import { defaultProfile, createSeedWorkspace } from '../src/seed';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');

describe('validateResumeText', () => {
  it('rejects wrong type', () => {
    const r = validateResumeText('x.pdf', 'hello');
    expect(r.ok).toBe(false);
  });
  it('rejects empty', () => {
    const r = validateResumeText('x.txt', '   ');
    expect(r.ok).toBe(false);
  });
  it('accepts txt', () => {
    expect(validateResumeText('a.txt', 'OSHA-30').ok).toBe(true);
  });
});

describe('scoreResume fixtures', () => {
  const profile = defaultProfile();

  it('scores rivera high with evidence', () => {
    const text = fs.readFileSync(path.join(root, 'fixtures/resumes/rivera.txt'), 'utf8');
    const resume = { id: 'r', filename: 'rivera.txt', rawText: text, importedAt: '', status: 'valid' as const };
    const result = scoreResume(resume, profile);
    expect(result.totalScore).toBeGreaterThanOrEqual(70);
    expect(result.matchedSkills).toContain('OSHA-30');
    expect(result.breakdown.every((b) => b.matched)).toBe(true);
    expect(result.breakdown[0].evidenceSpans.length).toBeGreaterThan(0);
  });

  it('scores chen at 0 with explanation', () => {
    const text = fs.readFileSync(path.join(root, 'fixtures/resumes/chen.txt'), 'utf8');
    const resume = { id: 'c', filename: 'chen.txt', rawText: text, importedAt: '', status: 'valid' as const };
    const result = scoreResume(resume, profile);
    expect(result.totalScore).toBe(0);
    expect(result.explanation).toMatch(/no criteria matched/i);
  });

  it('is deterministic', () => {
    const text = fs.readFileSync(path.join(root, 'fixtures/resumes/okonkwo.txt'), 'utf8');
    const resume = { id: 'o', filename: 'okonkwo.txt', rawText: text, importedAt: '', status: 'valid' as const };
    expect(scoreResume(resume, profile)).toEqual(scoreResume(resume, profile));
  });

  it('suggested buckets', () => {
    expect(suggestedBucket(90, { advance: 70, hold: 40 })).toBe('advance');
    expect(suggestedBucket(50, { advance: 70, hold: 40 })).toBe('hold');
    expect(suggestedBucket(10, { advance: 70, hold: 40 })).toBe('reject');
  });
});

describe('seed workspace', () => {
  it('ships 3 resumes scored', () => {
    const ws = createSeedWorkspace();
    expect(ws.resumes).toHaveLength(3);
    expect(ws.results).toHaveLength(3);
    expect(ws.decisions).toHaveLength(3);
  });
});
