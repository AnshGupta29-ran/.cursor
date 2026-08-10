/* ReviewHub SPA — vanilla JS, hash routing.
   Reasoning for no framework: the app is one data graph (PR -> files -> comments)
   and a handful of screens. A framework would add build tooling; here every
   re-render is a single renderRoute() call from fresh server state, so there is
   no client-side cache to keep consistent — the server is the source of truth. */

const $ = sel => document.querySelector(sel);
const view = $('#view');

// --- Auth token + fetch wrapper -------------------------------------------
// Token in localStorage: survives refresh (review sessions span days). XSS
// would exfiltrate it, which is exactly why ALL user content below goes through
// textContent/DOM APIs, never innerHTML.
const auth = {
  get token() { return localStorage.getItem('rh_token'); },
  set token(v) { v ? localStorage.setItem('rh_token', v) : localStorage.removeItem('rh_token'); }
};

async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    method: opts.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(auth.token ? { Authorization: 'Bearer ' + auth.token } : {})
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) { auth.token = null; location.hash = '#/login'; throw new Error('session expired'); }
  if (!res.ok) throw new Error(data.error || `request failed (${res.status})`);
  return data;
}

// --- DOM helpers: textContent everywhere = injection-proof by construction --
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  node.append(...children);
  return node;
}
const escTime = iso => new Date(iso.replace(' ', 'T') + 'Z').toLocaleString();
function toast(msg) {
  const t = $('#toast');
  t.textContent = msg; t.hidden = false;
  setTimeout(() => { t.hidden = true; }, 3000);
}

// --- WebSocket: one socket, two message types ------------------------------
// pr.update -> re-render if viewing that PR. notification -> bump the badge.
// Reconnect with backoff because review sessions are long-lived.
let ws = null, currentPRId = null;
function connectWS() {
  if (!auth.token || (ws && ws.readyState <= 1)) return;
  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws?token=${auth.token}`);
  ws.onopen = () => { if (currentPRId) ws.send(JSON.stringify({ type: 'subscribe', prId: currentPRId })); };
  ws.onmessage = e => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'pr.update' && msg.prId === currentPRId) renderPRDetail(msg.prId, true);
    if (msg.type === 'notification') { loadNotifBadge(); toast(msg.notification.message); }
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}

// --- Router -----------------------------------------------------------------
const routes = {
  '/login': renderLogin, '/register': renderRegister,
  '/dashboard': renderDashboard, '/prs': renderPRList
};
async function renderRoute() {
  const hash = location.hash.slice(1) || '/dashboard';
  const prMatch = hash.match(/^\/prs\/(\d+)$/);
  const authed = !!auth.token;
  $('#topbar').hidden = !authed;
  if (!authed && hash !== '/register') return renderLogin();
  if (prMatch) return renderPRDetail(Number(prMatch[1]));
  (routes[hash] || renderDashboard)();
}
window.addEventListener('hashchange', renderRoute);

// --- Auth views ---------------------------------------------------------------
function renderLogin() {
  const err = el('p', { class: 'error' });
  const form = el('form', { class: 'card auth-box' },
    el('h2', { text: 'Sign in to ReviewHub' }),
    el('input', { id: 'u', placeholder: 'username or email', required: '' }),
    el('input', { id: 'p', type: 'password', placeholder: 'password', required: '' }),
    err,
    el('button', { class: 'primary', text: 'Sign in' }),
    el('p', { class: 'muted', style: 'margin-top:10px' }, 'No account? ',
      el('a', { href: '#/register', text: 'Register' })));
  form.onsubmit = async e => {
    e.preventDefault(); err.textContent = '';
    try {
      const { token } = await api('/auth/login', { method: 'POST', body: { username: $('#u').value, password: $('#p').value } });
      auth.token = token; location.hash = '#/dashboard'; boot();
    } catch (ex) { err.textContent = ex.message; }
  };
  view.replaceChildren(form);
}

function renderRegister() {
  const err = el('p', { class: 'error' });
  const form = el('form', { class: 'card auth-box' },
    el('h2', { text: 'Create account' }),
    el('input', { id: 'u', placeholder: 'username', required: '' }),
    el('input', { id: 'e', type: 'email', placeholder: 'email', required: '' }),
    el('input', { id: 'p', type: 'password', placeholder: 'password (8+ chars)', required: '' }),
    err,
    el('button', { class: 'primary', text: 'Register' }),
    el('p', { class: 'muted', style: 'margin-top:10px' }, 'Have an account? ',
      el('a', { href: '#/login', text: 'Sign in' })));
  form.onsubmit = async e => {
    e.preventDefault(); err.textContent = '';
    try {
      const { token } = await api('/auth/register', { method: 'POST',
        body: { username: $('#u').value, email: $('#e').value, password: $('#p').value } });
      auth.token = token; location.hash = '#/dashboard'; boot();
    } catch (ex) { err.textContent = ex.message; }
  };
  view.replaceChildren(form);
}

// --- Dashboard: team picker + analytics + create-team -----------------------
async function renderDashboard() {
  currentPRId = null;
  const teams = await api('/teams');
  const card = el('div', { class: 'card' }, el('h2', { text: 'Your teams' }));
  if (!teams.length) card.append(el('p', { class: 'muted', text: 'No teams yet — create one below.' }));
  const sel = el('select');
  for (const t of teams) sel.append(el('option', { value: t.id, text: `${t.name} (${t.role})` }));
  if (teams.length) card.append(el('div', { class: 'row' }, sel));

  const createForm = el('form', { class: 'row', style: 'margin-top:12px' },
    el('input', { id: 'team-name', placeholder: 'new team name', required: '' }),
    el('button', { class: 'primary', text: 'Create team' }));
  createForm.onsubmit = async e => {
    e.preventDefault();
    try { await api('/teams', { method: 'POST', body: { name: $('#team-name').value } }); renderDashboard(); }
    catch (ex) { toast(ex.message); }
  };
  card.append(createForm);

  const analyticsCard = el('div', { class: 'card' }, el('h2', { text: 'Team analytics' }));
  async function loadAnalytics(teamId) {
    if (!teamId) { analyticsCard.append(el('p', { class: 'muted', text: 'Create a team to see analytics.' })); return; }
    let a;
    try { a = await api(`/teams/${teamId}/analytics`); }
    catch (ex) { analyticsCard.append(el('p', { class: 'error', text: ex.message })); return; }
    const approved = a.reviewStates.find(s => s.state === 'approved')?.n || 0;
    const changeReq = a.reviewStates.find(s => s.state === 'changes_requested')?.n || 0;
    const approvalRate = approved + changeReq ? Math.round(100 * approved / (approved + changeReq)) : null;
    const metrics = el('div', { class: 'row' },
      metric(a.totals.total, 'total PRs'),
      metric(a.totals.open, 'open'),
      metric(a.totals.merged, 'merged'),
      metric(a.avgHoursToFirstReview ? a.avgHoursToFirstReview.toFixed(1) + 'h' : '—', 'avg to first review'),
      metric(approvalRate === null ? '—' : approvalRate + '%', 'approval rate'));
    const stale = el('div');
    stale.append(el('h3', { text: 'Oldest open PRs (stale review risk)' }));
    if (!a.openAges.length) stale.append(el('p', { class: 'muted', text: 'No open PRs.' }));
    for (const pr of a.openAges) {
      stale.append(el('div', { class: 'list-row' },
        el('a', { href: `#/prs/${pr.id}`, text: `${pr.repo_name}#${pr.number} ${pr.title}` }),
        el('span', { class: 'muted', text: `${pr.age_hours}h by ${pr.author_name}` })));
    }
    const load = el('div');
    load.append(el('h3', { text: 'Reviewer load' }));
    const max = Math.max(1, ...a.reviewerLoad.map(r => r.reviews_done));
    for (const r of a.reviewerLoad) {
      load.append(el('div', { style: 'margin:6px 0' },
        el('div', { class: 'row' }, el('span', { text: r.username }),
          el('span', { class: 'muted', text: `${r.reviews_done} reviews, ${r.change_requests} change requests` })),
        el('div', { class: 'bar' }, el('div', { style: `width:${Math.round(100 * r.reviews_done / max)}%` }))));
    }
    analyticsCard.replaceChildren(el('h2', { text: 'Team analytics' }), metrics, stale, load);
  }
  if (teams.length) sel.onchange = () => loadAnalytics(Number(sel.value));
  view.replaceChildren(card, analyticsCard);
  loadAnalytics(teams[0]?.id);
}
const metric = (num, label) => el('div', { class: 'metric' },
  el('div', { class: 'num', text: String(num) }), el('div', { class: 'muted', text: label }));

// --- PR list + creation -------------------------------------------------------
async function renderPRList() {
  currentPRId = null;
  let status = 'open';
  const tabs = el('div', { class: 'tabs' },
    ...['open', 'merged', 'closed'].map(s =>
      el('button', { text: s, class: s === status ? 'active' : '', onclick: () => { status = s; reload(); } })));
  const listCard = el('div', { class: 'card' }, el('h2', { text: 'Pull requests' }));

  async function reload() {
    tabs.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.textContent === status));
    const prs = await api('/prs?status=' + status);
    const rows = prs.length ? prs.map(pr => el('div', { class: 'list-row' },
      el('div', {},
        el('a', { href: `#/prs/${pr.id}`, text: `${pr.repo_name}#${pr.number} — ${pr.title}` }),
        el('div', { class: 'muted', text: `by ${pr.author_name} · ${escTime(pr.created_at)}` })),
      el('div', { class: 'row' },
        pr.my_review ? el('span', { class: 'badge ' + pr.my_review, text: 'you: ' + pr.my_review.replace('_', ' ') }) : '',
        el('span', { class: 'badge ' + pr.status, text: pr.status }))))
      : [el('p', { class: 'muted', text: `No ${status} PRs.` })];
    listCard.replaceChildren(el('h2', { text: 'Pull requests' }), ...rows);
  }

  // Create-PR form: pick team -> pick repo -> paste unified diff per file.
  const teams = await api('/teams');
  const teamSel = el('select'), repoSel = el('select');
  for (const t of teams) teamSel.append(el('option', { value: t.id, text: t.name }));
  async function loadRepos() {
    repoSel.replaceChildren();
    if (!teamSel.value) return;
    const repos = await api(`/teams/${teamSel.value}/repos`);
    for (const r of repos) repoSel.append(el('option', { value: r.id, text: r.name }));
  }
  teamSel.onchange = loadRepos;

  const createCard = el('div', { class: 'card' }, el('h2', { text: 'Open a pull request' }));
  const err = el('p', { class: 'error' });
  const form = el('form', {},
    el('div', { class: 'row', style: 'margin-bottom:8px' }, teamSel, repoSel),
    el('input', { id: 'pr-title', placeholder: 'PR title', required: '', style: 'width:100%;margin-bottom:8px' }),
    el('textarea', { id: 'pr-desc', placeholder: 'Description', style: 'width:100%;min-height:50px;margin-bottom:8px' }),
    el('input', { id: 'pr-file', placeholder: 'file path (e.g. src/app.js)', required: '', style: 'width:100%;margin-bottom:8px' }),
    el('textarea', { id: 'pr-patch', placeholder: 'unified diff (@@ hunks, + / - lines)', required: '', style: 'width:100%;min-height:120px;font-family:monospace;margin-bottom:8px' }),
    err, el('button', { class: 'primary', text: 'Create PR' }));
  form.onsubmit = async e => {
    e.preventDefault(); err.textContent = '';
    if (!repoSel.value) { err.textContent = 'create a repository first (see below)'; return; }
    try {
      const { id } = await api(`/repos/${repoSel.value}/prs`, { method: 'POST', body: {
        title: $('#pr-title').value, description: $('#pr-desc').value,
        files: [{ path: $('#pr-file').value, patch: $('#pr-patch').value }] } });
      location.hash = `#/prs/${id}`;
    } catch (ex) { err.textContent = ex.message; }
  };

  const repoForm = el('form', { class: 'row', style: 'margin-top:14px' },
    el('input', { id: 'repo-name', placeholder: 'new repo name', required: '' }),
    el('button', { text: 'Add repo to selected team' }));
  repoForm.onsubmit = async e => {
    e.preventDefault();
    if (!teamSel.value) return toast('create a team first');
    try { await api(`/teams/${teamSel.value}/repos`, { method: 'POST', body: { name: $('#repo-name').value } }); loadRepos(); }
    catch (ex) { toast(ex.message); }
  };
  createCard.append(form, repoForm);
  view.replaceChildren(tabs, listCard, createCard);
  await loadRepos();
  await reload();
}

// --- PR detail: diff viewer + comments + reviews -----------------------------
// The heart of the product. parsePatch() converts unified diff text into a
// line model ONCE; both the table renderer and the comment-anchoring logic
// consume that model, so they can never disagree about line numbers.
function parsePatch(patch) {
  const lines = [];
  let newLine = 0;
  for (const raw of patch.split('\n')) {
    const hunk = raw.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunk) { newLine = Number(hunk[1]); lines.push({ type: 'hunk', text: raw, newLine: null }); continue; }
    if (raw.startsWith('+++') || raw.startsWith('---') || raw.startsWith('diff ') || raw.startsWith('index ')) continue;
    if (raw.startsWith('+')) lines.push({ type: 'add', text: raw, newLine: newLine++ });
    else if (raw.startsWith('-')) lines.push({ type: 'del', text: raw, newLine: null });
    else { lines.push({ type: 'ctx', text: raw, newLine: newLine++ }); }
  }
  return lines;
}

async function renderPRDetail(id, isRefresh = false) {
  let data;
  try { data = await api(`/prs/${id}`); }
  catch (ex) { view.replaceChildren(el('p', { class: 'error', text: ex.message })); return; }
  const { pr, files, comments, reviews, checklist, viewer } = data;
  if (currentPRId !== id) {
    currentPRId = id;
    if (ws?.readyState === 1) ws.send(JSON.stringify({ type: 'subscribe', prId: id }));
  }

  const root = el('div');

  // Header + actions. The merge button is shown only when the server says the
  // viewer CAN merge; clicking still re-validates server-side (defense in depth).
  const head = el('div', { class: 'card' },
    el('div', { class: 'row' },
      el('h2', { text: `${pr.repo_name}#${pr.number} ${pr.title}`, style: 'flex:1' }),
      el('span', { class: 'badge ' + pr.status, text: pr.status })),
    el('p', { class: 'muted', text: `${pr.author_name} wants to merge ${pr.source_branch} → ${pr.target_branch} · opened ${escTime(pr.created_at)}` }));
  if (pr.description) head.append(el('p', { style: 'margin-top:8px', text: pr.description }));

  const actions = el('div', { class: 'row', style: 'margin-top:12px' });
  if (pr.status === 'open') {
    if (!viewer.isAuthor) {
      for (const [state, label] of [['approved', 'Approve'], ['changes_requested', 'Request changes'], ['commented', 'Comment review']]) {
        actions.append(el('button', {
          text: label, class: state === 'approved' ? 'primary' : '',
          onclick: async () => {
            const body = state === 'approved' ? '' : prompt('Review comment (optional)') || '';
            try { await api(`/prs/${id}/reviews`, { method: 'POST', body: { state, body } }); renderPRDetail(id); }
            catch (ex) { toast(ex.message); }
          }
        }));
      }
    }
    if (viewer.canMerge) actions.append(el('button', { class: 'primary', text: 'Merge', onclick: () => prAction('merge') }));
    if (viewer.isAuthor || viewer.canMerge) actions.append(el('button', { class: 'danger', text: 'Close', onclick: () => prAction('close') }));
  } else if (viewer.isAuthor || viewer.canMerge) {
    actions.append(el('button', { text: 'Reopen', onclick: () => prAction('reopen') }));
  }
  async function prAction(action) {
    try { await api(`/prs/${id}/status`, { method: 'POST', body: { action } }); renderPRDetail(id); }
    catch (ex) { toast(ex.message); }
  }
  head.append(actions);

  if (reviews.length) {
    head.append(el('div', { class: 'row', style: 'margin-top:10px' },
      ...reviews.map(r => el('span', { class: 'badge ' + r.state, text: `${r.reviewer_name}: ${r.state.replace('_', ' ')}` }))));
  }

  // Checklist — the guidance mechanism for junior reviewers.
  const clCard = el('div', { class: 'card' }, el('h3', { text: 'Review checklist' }));
  for (const item of checklist) {
    const cb = el('input', { type: 'checkbox' });
    cb.checked = !!item.checked;
    cb.onchange = async () => { await api(`/checklist/${item.id}/toggle`, { method: 'POST' }); };
    clCard.append(el('label', { class: 'check-item' }, cb,
      el('span', { text: item.item, style: item.checked ? 'text-decoration:line-through' : '' })));
  }
  const clForm = el('form', { class: 'row', style: 'margin-top:8px' },
    el('input', { id: 'cl-item', placeholder: 'add checklist item', required: '' }),
    el('button', { text: 'Add' }));
  clForm.onsubmit = async e => {
    e.preventDefault();
    try { await api(`/prs/${id}/checklist`, { method: 'POST', body: { item: $('#cl-item').value } }); renderPRDetail(id); }
    catch (ex) { toast(ex.message); }
  };
  clCard.append(clForm);
  root.append(head, clCard);

  // Files + inline comments. Comments attach to NEW-file line numbers — that's
  // what the merged code will contain, so anchors stay meaningful after merge.
  const byAnchor = {};
  for (const c of comments) {
    const key = c.file_id ? `${c.file_id}:${c.line_number ?? 'file'}` : 'general';
    (byAnchor[key] ||= []).push(c);
  }
  const threadsOf = list => {
    // Thread rendering: roots in order, replies nested under their parent.
    const roots = list.filter(c => !c.parent_id);
    return roots.map(r => [r, ...list.filter(c => c.parent_id === r.id)]);
  };
  const commentView = (c, indent) => {
    const box = el('div', { class: 'comment' + (c.resolved ? ' resolved' : '') + (indent ? ' thread-indent' : '') },
      el('div', { class: 'meta', text: `${c.author_name} · ${escTime(c.created_at)}${c.resolved ? ' · resolved' : ''}` }),
      el('div', { text: c.body }));
    const row = el('div', { class: 'row', style: 'margin-top:6px' },
      el('button', { text: c.resolved ? 'Unresolve' : 'Resolve', onclick: async () => {
        try { await api(`/comments/${c.id}/resolve`, { method: 'POST' }); renderPRDetail(id); } catch (ex) { toast(ex.message); } } }),
      el('button', { text: 'Reply', onclick: () => {
        const body = prompt('Reply');
        if (body) api(`/prs/${id}/comments`, { method: 'POST', body: { body, parent_id: c.id } })
          .then(() => renderPRDetail(id)).catch(ex => toast(ex.message));
      } }));
    box.append(row);
    return box;
  };

  const filesCard = el('div', { class: 'card' }, el('h3', { text: `Files changed (${files.length})` }));
  for (const f of files) {
    filesCard.append(el('div', { class: 'file-head', text: f.path }));
    const table = el('table', { class: 'diff' });
    const tbody = el('tbody');
    for (const line of parsePatch(f.patch)) {
      const ln = el('td', { class: 'ln', text: line.newLine ?? '' });
      // Clicking a line number opens the inline comment form anchored there.
      if (line.newLine != null) ln.onclick = () => {
        const existing = tbody.querySelector('.inline-form');
        if (existing) existing.parentElement.remove();
        const ta = el('textarea', { placeholder: `Comment on line ${line.newLine}…` });
        const submit = el('button', { class: 'primary', text: 'Comment', onclick: async () => {
          if (!ta.value.trim()) return;
          try {
            await api(`/prs/${id}/comments`, { method: 'POST', body: { body: ta.value, file_id: f.id, line_number: line.newLine } });
            renderPRDetail(id);
          } catch (ex) { toast(ex.message); }
        } });
        const tr = el('tr', {}, el('td', { colspan: '2' },
          el('div', { class: 'inline-form' }, ta, submit)));
        lineRow.after(tr);
        ta.focus();
      };
      const lineRow = el('tr', { class: line.type === 'ctx' ? '' : line.type }, ln,
        el('td', { text: line.text }));
      tbody.append(lineRow);
    }
    table.append(tbody);
    filesCard.append(el('div', { class: 'diff-wrap' }, table));

    // Comments attached to this file render under it, grouped by line.
    for (const [key, list] of Object.entries(byAnchor)) {
      const [fid, lineNo] = key.split(':');
      if (Number(fid) !== f.id) continue;
      const anchor = el('p', { class: 'muted', text: lineNo === 'file' ? 'File-level comments' : `Line ${lineNo}` });
      filesCard.append(anchor);
      for (const thread of threadsOf(list)) {
        thread.forEach((c, i) => filesCard.append(commentView(c, i > 0)));
      }
    }
  }
  root.append(filesCard);

  // General discussion.
  const disc = el('div', { class: 'card' }, el('h3', { text: 'Discussion' }));
  for (const thread of threadsOf(byAnchor['general'] || [])) {
    thread.forEach((c, i) => disc.append(commentView(c, i > 0)));
  }
  const ta = el('textarea', { id: 'gen-body', placeholder: 'Leave a comment…' });
  disc.append(ta, el('button', { class: 'primary', text: 'Comment', onclick: async () => {
    if (!ta.value.trim()) return;
    try { await api(`/prs/${id}/comments`, { method: 'POST', body: { body: ta.value } }); renderPRDetail(id); }
    catch (ex) { toast(ex.message); }
  } }));
  root.append(disc);

  // WS refresh preserves scroll — losing your place mid-review is the worst UX.
  const y = isRefresh ? window.scrollY : 0;
  view.replaceChildren(root);
  window.scrollTo(0, y);
}

// --- Notifications -------------------------------------------------------------
async function loadNotifBadge() {
  if (!auth.token) return;
  const notifs = await api('/notifications').catch(() => []);
  const unread = notifs.filter(n => !n.read).length;
  const badge = $('#notif-badge');
  badge.hidden = unread === 0;
  badge.textContent = unread;
  $('#notif-list').replaceChildren(...(notifs.length ? notifs.map(n =>
    el('div', { class: n.read ? '' : 'unread' },
      el('div', { text: n.message }),
      el('div', { class: 'muted', style: 'font-size:11px', text: escTime(n.created_at) })))
    : [el('div', { class: 'muted', text: 'No notifications yet.' })]));
}
$('#notif-btn').onclick = () => { const p = $('#notif-panel'); p.hidden = !p.hidden; if (!p.hidden) loadNotifBadge(); };
$('#notif-read-all').onclick = async () => { await api('/notifications/read', { method: 'POST' }); loadNotifBadge(); };

$('#logout-btn').onclick = () => { auth.token = null; ws?.close(); ws = null; location.hash = '#/login'; renderRoute(); };

async function boot() {
  if (auth.token) {
    const me = await api('/auth/me').catch(() => null);
    if (me) $('#whoami').textContent = me.user.username;
    connectWS();
    loadNotifBadge();
  }
  renderRoute();
}
boot();
