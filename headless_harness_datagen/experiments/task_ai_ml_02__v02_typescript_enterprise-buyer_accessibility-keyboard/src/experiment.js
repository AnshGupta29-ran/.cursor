// Experiment model – lightweight representation of an ML run
// Fields mirror the TypeScript interface from the original design
/**
 * @typedef {Object} Experiment
 * @property {string} id - Unique identifier (UUID v4 style)
 * @property {string} name - Human‑readable experiment name
 * @property {string} [description] - Optional longer description
 * @property {string} createdAt - ISO‑8601 timestamp when created
 * @property {'running'|'completed'|'failed'} status - Current lifecycle state
 */

module.exports = {};
