import type { Workspace, RoleProfile, ResumeAsset } from './types';
import { scoreResume, suggestedBucket } from './engine';

const RIVERA = `Jordan Rivera
Journeyman track applicant — Industrial Maintenance

CERTIFICATIONS
- OSHA-30 Construction completed 2023
- NCCER Core Curriculum + Industrial Maintenance Level 1
- PLC basics certificate (Allen-Bradley intro)

EXPERIENCE
- 3 years millwright helper: hydraulics troubleshooting, reading schematics on press lines
- Apprenticeship cohort volunteer mentor at local training center

EDUCATION
- Community college workforce board certificate, Industrial Maintenance
`;

const OKONKWO = `Sam Okonkwo
Maintenance Technician Candidate

Experience
- Warehouse equipment repair; basic electrical
- Familiar with hydraulic systems on forklifts
- Can read blueprints for rack installs

Education
- Trade school diploma
- Interested in Programmable Logic Controller courses (not yet certified)

Notes
- Safety card pending next month
- No craft credential card yet
`;

const CHEN = `Alex Chen
Retail associate seeking career change

Skills
- Customer service, inventory counting
- Microsoft Office

Education
- High school diploma

No trades certifications listed.
`;

export function defaultProfile(): RoleProfile {
  return {
    id: 'profile-ima',
    name: 'Industrial Maintenance Apprentice',
    jobDescription:
      'Apprenticeship cohort for industrial maintenance: OSHA-30, PLC basics, hydraulics, NCCER, blueprint/schematic reading. Journeyman pathway via union training center.',
    criteria: [
      { skill: 'OSHA-30', synonyms: ['OSHA30', 'Occupational Safety and Health Administration'], weight: 10 },
      { skill: 'PLC basics', synonyms: ['Programmable Logic Controller', 'PLC'], weight: 8 },
      { skill: 'hydraulics', synonyms: ['hydraulic systems'], weight: 6 },
      { skill: 'NCCER', synonyms: [], weight: 5 },
      { skill: 'blueprint reading', synonyms: ['reading schematics', 'schematics'], weight: 7 },
    ],
    sectionWeights: { certifications: 1.2, experience: 1.0, education: 0.8 },
    thresholds: { advance: 70, hold: 40 },
  };
}

export function createSeedWorkspace(): Workspace {
  const profile = defaultProfile();
  const now = new Date().toISOString();
  const resumes: ResumeAsset[] = [
    { id: 'res-rivera', filename: 'rivera.txt', rawText: RIVERA, importedAt: now, status: 'valid' },
    { id: 'res-okonkwo', filename: 'okonkwo.txt', rawText: OKONKWO, importedAt: now, status: 'valid' },
    { id: 'res-chen', filename: 'chen.txt', rawText: CHEN, importedAt: now, status: 'valid' },
  ];
  const results = resumes.map((r) => scoreResume(r, profile));
  const decisions = results.map((res) => ({
    resumeId: res.resumeId,
    bucket: suggestedBucket(res.totalScore, profile.thresholds),
    decidedBy: 'system-suggest',
    timestamp: now,
    confirmed: false,
    note: 'auto-bucketed; human must confirm',
  }));

  return {
    version: 1,
    profiles: [profile],
    activeProfileId: profile.id,
    resumes,
    results,
    decisions,
    audit: [
      {
        type: 'seed',
        payload: { profile: profile.name, resumes: resumes.length },
        timestamp: now,
      },
    ],
  };
}
