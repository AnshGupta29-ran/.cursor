#!/usr/bin/env node
/**
 * MeritLens CLI — stateless folder screen.
 * Usage: node cli/cli.mjs screen --profile <file> --resumes <dir> [--json] [--out results.json]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Command } from 'commander';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function validateResumeText(filename, rawText) {
  const lower = filename.toLowerCase();
  if (!lower.endsWith('.txt') && !lower.endsWith('.md')) {
    return { ok: false, reason: `Unsupported file type for "${filename}" (only .txt / .md).` };
  }
  if (!rawText || !String(rawText).trim()) {
    return { ok: false, reason: `Empty file rejected: "${filename}".` };
  }
  const bytes = Buffer.byteLength(rawText, 'utf8');
  if (bytes > 200 * 1024) {
    return { ok: false, reason: `File too large (>200 KB): "${filename}".` };
  }
  return { ok: true };
}

function scoreResume(resume, profile) {
  const text = resume.rawText ?? '';
  const lower = text.toLowerCase();
  const breakdown = [];
  let totalPoints = 0;
  let maxPoints = 0;
  const matchedSkills = [];
  const missingSkills = [];

  for (const crit of profile.criteria) {
    const terms = [crit.skill, ...(crit.synonyms ?? [])].map((t) => t.toLowerCase()).filter(Boolean);
    let found = false;
    const spans = [];
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
    breakdown.push({ criterion: crit.skill, matched: found, evidenceSpans: spans, points });
    if (found) matchedSkills.push(crit.skill);
    else missingSkills.push(crit.skill);
  }

  const totalScore = maxPoints ? Math.round((totalPoints / maxPoints) * 1000) / 10 : 0;
  return {
    resumeId: resume.id,
    filename: resume.filename,
    totalScore,
    breakdown,
    matchedSkills,
    missingSkills,
    explanation:
      matchedSkills.length === 0
        ? 'no criteria matched — score 0; resume lacks rubric keywords/synonyms'
        : undefined,
  };
}

function suggestedBucket(score, thresholds) {
  if (score >= thresholds.advance) return 'advance';
  if (score >= thresholds.hold) return 'hold';
  return 'reject';
}

const program = new Command();
program.name('meritlens').description('Auditable resume screening for skilled-trades cohorts');

program
  .command('screen')
  .requiredOption('--profile <file>', 'Role profile JSON')
  .requiredOption('--resumes <dir>', 'Folder of .txt/.md resumes')
  .option('--json', 'Emit JSON to stdout')
  .option('--out <file>', 'Write results JSON to file')
  .action((opts) => {
    const profilePath = path.resolve(opts.profile);
    const resumesDir = path.resolve(opts.resumes);
    if (!fs.existsSync(profilePath)) {
      console.error(`Profile not found: ${profilePath}`);
      process.exit(1);
    }
    if (!fs.existsSync(resumesDir)) {
      console.error(`Resumes dir not found: ${resumesDir}`);
      process.exit(1);
    }
    const profile = JSON.parse(fs.readFileSync(profilePath, 'utf8'));
    profile.id = profile.id || profile.name || 'profile';
    profile.thresholds = profile.thresholds || { advance: 70, hold: 40 };

    const files = fs.readdirSync(resumesDir).filter((f) => /\.(txt|md)$/i.test(f));
    const ranked = [];
    const rejects = [];

    for (const file of files) {
      const full = path.join(resumesDir, file);
      const rawText = fs.readFileSync(full, 'utf8');
      const check = validateResumeText(file, rawText);
      if (!check.ok) {
        rejects.push({ filename: file, reason: check.reason });
        continue;
      }
      const resume = { id: file, filename: file, rawText };
      const result = scoreResume(resume, profile);
      ranked.push({
        ...result,
        bucket: suggestedBucket(result.totalScore, profile.thresholds),
      });
    }

    ranked.sort((a, b) => b.totalScore - a.totalScore);
    const payload = {
      profile: profile.name,
      ranked,
      rejects,
    };

    if (opts.out) {
      fs.writeFileSync(path.resolve(opts.out), JSON.stringify(payload, null, 2));
    }

    if (opts.json) {
      console.log(JSON.stringify(payload, null, 2));
    } else {
      console.log(`MeritLens screen — ${profile.name}`);
      console.log('filename\tscore\tbucket\tmatched');
      for (const r of ranked) {
        console.log(`${r.filename}\t${r.totalScore}\t${r.bucket}\t${r.matchedSkills.join('|')}`);
      }
      for (const r of rejects) {
        console.error(`REJECT ${r.filename}: ${r.reason}`);
      }
    }
  });

program.parse(process.argv);
