export interface SkillCriterion {
  skill: string;
  synonyms: string[];
  weight: number;
}

export interface RoleProfile {
  id: string;
  name: string;
  jobDescription?: string;
  criteria: SkillCriterion[];
  sectionWeights?: { [section: string]: number };
  thresholds: { advance: number; hold: number };
}

export interface ResumeAsset {
  id: string;
  filename: string;
  rawText: string;
  importedAt: string;
  status: 'valid' | 'invalid' | 'error';
  errorReason?: string;
}

export interface CriterionResult {
  criterion: string;
  matched: boolean;
  evidenceSpans: { start: number; end: number }[];
  points: number;
}

export interface ScreeningResult {
  resumeId: string;
  profileId: string;
  totalScore: number;
  breakdown: CriterionResult[];
  confidence: number;
  matchedSkills: string[];
  missingSkills: string[];
  explanation?: string;
}

export type Bucket = 'advance' | 'hold' | 'reject';

export interface ReviewDecision {
  resumeId: string;
  bucket: Bucket;
  decidedBy: string;
  timestamp: string;
  note?: string;
  confirmed: boolean;
}

export interface AuditEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface Workspace {
  version: 1;
  profiles: RoleProfile[];
  activeProfileId: string;
  resumes: ResumeAsset[];
  results: ScreeningResult[];
  decisions: ReviewDecision[];
  audit: AuditEvent[];
}

export type ViewId = 'queue' | 'detail' | 'roles';
