/**
 * Experiment domain model and helper functions.
 * An experiment records a name, a timestamp and optional metadata.
 */

export interface Experiment {
  id: string;
  name: string;
  createdAt: string; // ISO string
  metadata?: Record<string, unknown>;
}

/** Generate a new experiment object */
export function createExperiment(name: string, metadata?: Record<string, unknown>): Experiment {
  return {
    id: crypto.randomUUID?.() ?? Math.random().toString(36).substring(2, 15),
    name,
    createdAt: new Date().toISOString(),
    metadata,
  };
}
