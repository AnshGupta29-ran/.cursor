export interface Experiment {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed';
  startedAt: string;
  endedAt?: string;
  params: Record<string, any>;
  metrics: Record<string, number[]>;
}
