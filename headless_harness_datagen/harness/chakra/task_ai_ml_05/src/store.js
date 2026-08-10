// Simple in-memory store for Harborline Dispatch
// Used to avoid native SQLite dependencies for this datagen task.

let tickets = [];
let classifications = [];
let queues = [];
let auditLog = [];

export function initStore(routingConfig) {
  // Initialize static queues based on precedence if not already present
  if (queues.length === 0) {
    routingConfig.queuePrecedence.forEach((q, i) => {
      queues.push({
        name: q,
        description: `Queue for ${q}`,
        sla_minutes: 60,
        precedence: i,
      });
    });
  }
}

export function addTicket(ticket) {
  tickets.push(ticket);
}

export function addClassification(classif) {
  classifications.push(classif);
}

export function getTicketsByCategory(category) {
  const ids = classifications
    .filter(c => c.category === category)
    .map(c => c.ticket_id);
  return tickets.filter(t => ids.includes(t.id));
}

export function getStats(reviewThreshold) {
  const total = tickets.length;
  const perQueue = classifications.reduce((acc, c) => {
    acc[c.category] = (acc[c.category] || 0) + 1;
    return acc;
  }, {});
  const urgencyHist = classifications.reduce((acc, c) => {
    acc[c.urgency] = (acc[c.urgency] || 0) + 1;
    return acc;
  }, {});
  const reviewCount = classifications.filter(c => c.confidence < reviewThreshold).length;
  return { total, perQueue, urgencyHist, reviewCount };
}

export function exportBundle() {
  return {
    version: 1,
    tickets,
    classifications,
    queues,
    audit: auditLog,
  };
}

export function importBundle(bundle) {
  if (!bundle || bundle.version !== 1) {
    throw new Error('Invalid bundle');
  }
  tickets = bundle.tickets || [];
  classifications = bundle.classifications || [];
  queues = bundle.queues || [];
  auditLog = bundle.audit || [];
}
