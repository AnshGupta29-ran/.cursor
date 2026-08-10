// Simple deterministic keyword‑based scorer for MeritLens
// Returns a totalScore (0‑100) and a breakdown of matched criteria.

const SKILL_LEXICON = {
  "kubernetes": {category: "backend", weight: 15},
  "docker": {category: "devops", weight: 10},
  "react": {category: "frontend", weight: 10},
  "typescript": {category: "frontend", weight: 5},
  "aws": {category: "cloud", weight: 12},
  "leadership": {category: "leadership", weight: 20},
  "team": {category: "leadership", weight: 5},
  // add more as needed
};

export function scoreResume(text) {
  const lower = text.toLowerCase();
  let total = 0;
  const breakdown = [];
  for (const [term, info] of Object.entries(SKILL_LEXICON)) {
    const regex = new RegExp(`\\b${term}\\b`, "gi");
    const matches = lower.match(regex);
    if (matches) {
      const count = matches.length;
      const pts = info.weight * Math.min(count, 3); // cap per term
      total += pts;
      breakdown.push({term, category: info.category, count, points: pts});
    }
  }
  total = Math.min(total, 100);
  return {totalScore: total, breakdown};
}
