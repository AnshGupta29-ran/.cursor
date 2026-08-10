const QUEUES = ['safety', 'fare-billing', 'fleet-damage', 'accessibility', 'general', 'review'];
let activeQueue = 'safety';

const healthEl = document.getElementById('health');
const tabsEl = document.getElementById('queue-tabs');
const listEl = document.getElementById('queue-list');
const statsEl = document.getElementById('stats');
const resultEl = document.getElementById('result');

QUEUES.forEach((q) => {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = q;
  b.dataset.q = q;
  if (q === activeQueue) b.classList.add('active');
  b.addEventListener('click', () => {
    activeQueue = q;
    [...tabsEl.children].forEach((c) => c.classList.toggle('active', c.dataset.q === q));
    loadQueue();
  });
  tabsEl.appendChild(b);
});

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) },
    ...opts,
  });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
  if (!res.ok) throw Object.assign(new Error(data?.error?.message || res.statusText), { status: res.status, data });
  return data;
}

async function refreshHealth() {
  try {
    const h = await api('/health');
    healthEl.textContent = `API ${h.status}`;
    healthEl.style.color = '#8dffb0';
  } catch {
    healthEl.textContent = 'API down';
    healthEl.style.color = '#ffb4b4';
  }
}

async function loadQueue() {
  listEl.textContent = 'Loading…';
  try {
    const rows = await api(`/queues/${encodeURIComponent(activeQueue)}/tickets`);
    if (!rows.length) {
      listEl.innerHTML = `<div class="muted">No tickets in <strong>${activeQueue}</strong>.</div>`;
      return;
    }
    listEl.innerHTML = rows.map((t) => `
      <article class="card">
        <div><strong>${escapeHtml(t.subject || '(no subject)')}</strong> · ${escapeHtml(t.status || '')}</div>
        <div class="muted">${escapeHtml(t.channel || '')} · ${escapeHtml(t.author_handle || '')} · ${escapeHtml(t.created_at || '')}</div>
        <div>${escapeHtml(t.body || '')}</div>
      </article>`).join('');
  } catch (e) {
    listEl.innerHTML = `<div class="muted">Queue load failed: ${escapeHtml(e.message)}</div>`;
  }
}

async function loadStats() {
  try {
    const s = await api('/stats');
    statsEl.textContent = JSON.stringify(s, null, 2);
  } catch (e) {
    statsEl.textContent = `stats failed: ${e.message}`;
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

document.getElementById('ticket-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  const payload = Object.fromEntries(fd.entries());
  resultEl.classList.remove('hidden');
  resultEl.textContent = 'Classifying…';
  try {
    const out = await api('/tickets', { method: 'POST', body: JSON.stringify(payload) });
    const evd = (out.evidence || []).map((e) => `<span class="chip">${escapeHtml(e.type)}:${escapeHtml(e.term)}</span>`).join('');
    resultEl.innerHTML = `
      <div><strong>Ticket</strong> ${escapeHtml(out.id || out.ticket_id || '')} · status ${escapeHtml(out.status || '')}</div>
      <div>sentiment <strong>${escapeHtml(out.sentiment)}</strong> · urgency <strong>${escapeHtml(out.urgency)}</strong> · category <strong>${escapeHtml(out.category)}</strong></div>
      <div>confidence ${(Number(out.confidence) || 0).toFixed(3)}${out.suggested_queue ? ` · suggested ${escapeHtml(out.suggested_queue)}` : ''}</div>
      <div style="margin-top:0.4rem">${evd || '<span class="muted">no evidence terms</span>'}</div>`;
    activeQueue = out.status === 'review' ? 'review' : (out.category || activeQueue);
    [...tabsEl.children].forEach((c) => c.classList.toggle('active', c.dataset.q === activeQueue));
    await Promise.all([loadQueue(), loadStats()]);
  } catch (e) {
    resultEl.innerHTML = `<div style="color:var(--bad)">Error ${e.status || ''}: ${escapeHtml(e.message)}</div>`;
  }
});

const SAMPLES = [
  { channel: 'kiosk', author_handle: '@maya', subject: 'Pier 4 gate', body: 'the dock gate at Pier 4 is jammed and my card was charged twice' },
  { channel: 'sms', author_handle: '+1555', subject: 'Fare refund', body: 'please refund the fare card double charge from this morning thank you' },
  { channel: 'email', author_handle: 'a@b.co', subject: 'Bike damage', body: 'shared bike at Station 12 has a bent wheel and broken brake, fleet damaged' },
  { channel: 'kiosk', author_handle: '@lee', subject: 'Ramp access', body: 'wheelchair ramp at Pier 2 elevator is blocked, accessibility issue for boarding' },
];

document.getElementById('seed-btn').addEventListener('click', async () => {
  for (const s of SAMPLES) {
    try { await api('/tickets', { method: 'POST', body: JSON.stringify(s) }); } catch { /* continue */ }
  }
  await Promise.all([loadQueue(), loadStats()]);
  resultEl.classList.remove('hidden');
  resultEl.innerHTML = '<div>Seeded sample rider tickets across queues.</div>';
});

document.getElementById('refresh-btn').addEventListener('click', () => Promise.all([refreshHealth(), loadQueue(), loadStats()]));
document.getElementById('export-btn').addEventListener('click', async () => {
  const data = await api('/export');
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'harborline-export.json';
  a.click();
});

refreshHealth();
loadQueue();
loadStats();
