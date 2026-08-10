import type { RoleProfile, ResumeAsset, ScreeningResult, CriterionResult, Bucket } from './types';

const MAX_BYTES = 200 * 1024;

export function validateResumeText(
  filename: string,
  rawText: string
): { ok: true } | { ok: false; reason: string } {
  const lower = filename.toLowerCase();
  if (!lower.endsWith('.txt') && !lower.endsWith('.md')) {
    return { ok: false, reason: `Unsupported file type for "${filename}" (only .txt / .md).` };
  }
  if (!rawText || !rawText.trim()) {
    return { ok: false, reason: `Empty file rejected: "${filename}".` };
  }
  const bytes = new TextEncoder().encode(rawText).length;
  if (bytes > MAX_BYTES) {
    return { ok: false, reason: `File too large (>200 KB): "${filename}".` };
  }
  return { ok: true };
}

/**
 * Deterministic rubric scorer — keyword + synonym match with evidence spans.
 */
export function scoreResume(resume: ResumeAsset, profile: RoleProfile): ScreeningResult {
  const text = resume.rawText ?? '';
  const lower = text.toLowerCase();
  const breakdown: CriterionResult[] = [];
  let totalPoints = 0;
  let maxPoints = 0;
  const matchedSkills: string[] = [];
  const missingSkills: string[] = [];

  for (const crit of profile.criteria) {
    const terms = [crit.skill, ...(crit.synonyms ?? [])]
      .map((t) => t.toLowerCase())
      .filter(Boolean);
    let found = false;
    const spans: { start: number; end: number }[] = [];
    for (const term of terms) {
      const idx = lower.indexOf(term);
      if (idx !== -1) {
        found = true;
        spans.push({ start: idx, end: idx + term.length });
        break;
      }
    }
    const points = found ? crit.weight : 0;
    totalPoints += points;
    maxPoints += crit.weight;
    breakdown.push({
      criterion: crit.skill,
      matched: found,
      evidenceSpans: spans,
      points,
    });
    if (found) matchedSkills.push(crit.skill);
    else missingSkills.push(crit.skill);
  }

  const totalScore = maxPoints ? Math.round((totalPoints / maxPoints) * 1000) / 10 : 0;
  const confidence = maxPoints ? Math.round((matchedSkills.length / profile.criteria.length) * 100) / 100 : 0;

  return {
    resumeId: resume.id,
    profileId: profile.id,
    totalScore,
    breakdown,
    confidence,
    matchedSkills,
    missingSkills,
    explanation:
      matchedSkills.length === 0
        ? 'no criteria matched — score 0; resume lacks rubric keywords/synonyms'
        : undefined,
  };
}

export function suggestedBucket(score: number, thresholds: RoleProfile['thresholds']): Bucket {
  if (score >= thresholds.advance) return 'advance';
  if (score >= thresholds.hold) return 'hold';
  return 'reject';
}

export const THRESHOLD_PRESETS = {
  strict: { advance: 80, hold: 55 },
  'open-cohort': { advance: 60, hold: 30 },
} as const;
