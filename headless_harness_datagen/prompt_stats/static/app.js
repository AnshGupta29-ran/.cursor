/* Agent Prompt Analytics frontend (Chakra + Pi) */
(() => {
  const state = {
    records: [],
    usage: null,
    kimi: null,
    dims: null,
    charts: {},
    page: "ledger",
    pollMs: 8000,
  };

  const $ = (id) => document.getElementById(id);

  function fmtTokens(n, estimated = false) {
    if (n == null || Number.isNaN(n)) return "—";
    n = Number(n);
    let s;
    if (n >= 1_000_000) s = (n / 1_000_000).toFixed(2) + "M";
    else if (n >= 10_000) s = (n / 1000).toFixed(1) + "k";
    else if (n >= 1000) s = (n / 1000).toFixed(2) + "k";
    else s = String(Math.round(n));
    return estimated ? `~${s}` : s;
  }

  function fmtTime(sec) {
    if (sec == null || Number.isNaN(sec)) return "—";
    sec = Number(sec);
    if (sec < 60) return `${sec.toFixed(0)}s`;
    if (sec < 3600) return `${(sec / 60).toFixed(1)}m`;
    const h = Math.floor(sec / 3600);
    const m = Math.round((sec % 3600) / 60);
    return `${h}h ${m}m`;
  }

  function whenOf(r) {
    return r.event_time || r.recorded_at || "";
  }

  function agentOf(r) {
    if (r.agent === "pi" || r.agent === "chakra") return r.agent;
    const src = String(r.source || "");
    if (src.startsWith("pi_")) return "pi";
    if (src.startsWith("chakra_") || src === "pipeline" || src === "forge") return "chakra";
    return "other";
  }


  function chargedIn(r) {
    if (r.input_tokens_api != null) return Number(r.input_tokens_api);
    if (r.tokens_are_estimated === true) return 0;
    if (r.input_tokens != null) return Number(r.input_tokens);
    return 0;
  }
  function chargedOut(r) {
    if (r.output_tokens_api != null) return Number(r.output_tokens_api);
    if (r.tokens_are_estimated === true) return 0;
    if (r.output_tokens != null) return Number(r.output_tokens);
    return 0;
  }
  function estIn(r) {
    if (r.input_tokens_est != null) return Number(r.input_tokens_est);
    if (r.tokens_are_estimated === true && r.input_tokens != null) return Number(r.input_tokens);
    if (r.est_tokens != null && r.tokens_are_estimated === true) return Number(r.est_tokens);
    return 0;
  }
  function estOut(r) {
    if (r.output_tokens_est != null) return Number(r.output_tokens_est);
    if (r.tokens_are_estimated === true && r.output_tokens != null) return Number(r.output_tokens);
    return 0;
  }
  function isTokEst(r) {
    if (r.tokens_are_estimated === true) return true;
    if (r.input_tokens != null || r.output_tokens != null) return false;
    return r.input_tokens_est != null || r.output_tokens_est != null;
  }

  function inputTokens(r) {
    // Prefer estimates when marked estimated (sparse API usage can under-count)
    if (r.tokens_are_estimated === true) {
      if (r.input_tokens_est != null) return Number(r.input_tokens_est);
      if (r.est_tokens != null) return Number(r.est_tokens);
    }
    if (r.input_tokens != null) return Number(r.input_tokens);
    if (r.input_tokens_est != null) return Number(r.input_tokens_est);
    if (r.est_tokens != null) return Number(r.est_tokens);
    return null;
  }

  function outputTokens(r) {
    if (r.tokens_are_estimated === true) {
      if (r.output_tokens_est != null) return Number(r.output_tokens_est);
    }
    if (r.output_tokens != null) return Number(r.output_tokens);
    if (r.output_tokens_est != null) return Number(r.output_tokens_est);
    return null;
  }

  function totalTokens(r) {
    if (r.total_tokens != null) return Number(r.total_tokens);
    if (r.total_tokens_est != null) return Number(r.total_tokens_est);
    const a = inputTokens(r);
    const b = outputTokens(r);
    if (a == null && b == null) return null;
    return (a || 0) + (b || 0);
  }

  function filtered() {
    const agent = $("filterAgent") ? $("filterAgent").value : "";
    const src = $("filterSource").value;
    const model = $("filterModel") ? $("filterModel").value : "";
    const band = $("filterBand").value;
    const q = $("filterQ").value.trim().toLowerCase();
    return state.records
      .filter((r) => !agent || agentOf(r) === agent)
      .filter((r) => !src || r.source === src)
      .filter((r) => {
        if (!model) return true;
        if (r.model !== model) return false;
        // With a model selected and no explicit source, show only model slices
        // so table rows Σ == KPI Σ == by-model card (no session double-count).
        if (!src && String(r.source || "").endsWith("_session")) return false;
        return true;
      })
      .filter((r) => !band || r.complexity_band === band)
      .filter((r) => {
        if (!q) return true;
        const hay = `${r.title || ""} ${r.seed || ""} ${r.category || ""} ${r.model || ""} ${agentOf(r)}`.toLowerCase();
        return hay.includes(q);
      })
      .sort((a, b) => (whenOf(b) || "").localeCompare(whenOf(a) || ""));
  }

  function destroyCharts() {
    Object.values(state.charts).forEach((c) => c.destroy());
    state.charts = {};
  }

  function chartDefaults() {
    Chart.defaults.color = "#7f9aa8";
    Chart.defaults.borderColor = "#1e3a48";
    Chart.defaults.font.family = "DM Sans";
  }

  /** Session / pipeline rows only — excludes *_model slices (avoids double-count). */
  function primaryStatRows(rows) {
    return rows.filter((r) => {
      const s = String(r.source || "");
      if (s.endsWith("_model")) return false;
      return (
        s.endsWith("_session") ||
        s === "pipeline" ||
        s === "chakra_history" ||
        s === "forge"
      );
    });
  }

  /** Token/time pool: prefer model slices when a model filter is active. */
  function tokenStatRows(rows) {
    const model = $("filterModel") ? $("filterModel").value : "";
    const slices = rows.filter((r) => String(r.source || "").endsWith("_model"));
    if (model && slices.length) return slices;
    const sessions = primaryStatRows(rows);
    if (sessions.length) return sessions;
    return rows.filter((r) => !String(r.source || "").endsWith("_model"));
  }

  function renderKpis(rows) {
    const kpiPool = tokenStatRows(rows);
    const model = $("filterModel") ? $("filterModel").value : "";
    const scores = rows.map((r) => r.complexity_score).filter((x) => x != null);
    const outs = kpiPool.map(outputTokens).filter((x) => x != null);
    const times = kpiPool
      .map((r) => r.runtime_seconds)
      .filter((x) => typeof x === "number");
    const avg = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);
    const sumOut = outs.reduce((a, b) => a + b, 0);
    const agents = new Set(rows.map(agentOf).filter((a) => a === "chakra" || a === "pi"));
    const poolHint = model
      ? `Σ of ${kpiPool.length} ${model} model slices (matches by-model card)`
      : "sessions only — no model-slice double-count";

    const sumCharged = kpiPool.reduce((a, r) => a + chargedIn(r) + chargedOut(r), 0);
    const sumEst = kpiPool.reduce((a, r) => a + estIn(r) + estOut(r), 0);
    const cards = [
      { label: "Records", value: rows.length, hint: "matching filters (table rows)" },
      { label: "Agents", value: agents.size || "—", hint: [...agents].join(" · ") || "none in view" },
      { label: "Avg complexity", value: avg(scores)?.toFixed(1) ?? "—", hint: "0–100 score" },
      { label: "Charged Σ", value: fmtTokens(sumCharged || null), hint: "exact only (often 0)", cls: "good" },
      { label: "Estimate Σ", value: fmtTokens(sumEst || null, true), hint: "NOT a bill", cls: "warn" },
      { label: "Avg output tok", value: fmtTokens(avg(outs), true), hint: model ? "per model slice" : "per session" },
      { label: "Avg time", value: fmtTime(avg(times)), hint: "wall clock" },
      {
        label: "Total time Σ",
        value: fmtTime(times.reduce((a, b) => a + b, 0) || null),
        hint: model ? "model-slice active spans" : "session wall clocks",
      },
    ];
    $("kpis").innerHTML = cards
      .map(
        (c) =>
          `<div class="kpi ${c.cls || ""}"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></div>`
      )
      .join("");
  }

  function renderTable(rows) {
    $("tbody").innerHTML = rows
      .map((r) => {
        const band = r.complexity_band || "low";
        const agent = agentOf(r);
        return `<tr>
          <td class="mono">${(whenOf(r) || "").slice(0, 19)}</td>
          <td><span class="agent-pill ${agent}">${escapeHtml(agent)}</span></td>
          <td class="mono">${escapeHtml(r.model || "—")}</td>
          <td>${r.source || "—"}</td>
          <td>${escapeHtml(r.category || "—")}</td>
          <td><span class="band ${band}">${band}</span></td>
          <td class="mono">${r.complexity_score != null ? Number(r.complexity_score).toFixed(1) : "—"}</td>
          <td class="mono">${fmtTokens(chargedIn(r) + chargedOut(r))}${chargedIn(r)+chargedOut(r)>0 ? ' <span class="band exact">exact</span>' : ''}</td>
          <td class="mono">${fmtTokens(estIn(r), true)}</td>
          <td class="mono">${fmtTokens(estOut(r), true)}</td>
          <td class="mono">${fmtTime(r.runtime_seconds)}</td>
          <td class="mono">${r.tool_calls ?? "—"}</td>
          <td class="title-cell">${escapeHtml((r.title || "").slice(0, 120))}</td>
        </tr>`;
      })
      .join("");
  }

  function sessionRows(rows) {
    return rows.filter((r) => {
      const s = r.source || "";
      return s.endsWith("_session") || s === "pipeline";
    });
  }

  function aggregateByAgent(allRows) {
    const pool = sessionRows(allRows);
    const by = {};
    for (const r of pool) {
      const a = agentOf(r);
      if (a === "other") continue;
      if (!by[a]) {
        by[a] = {
          agent: a,
          sessions: 0,
          outTok: 0,
          inTok: 0,
          timeSec: 0,
          models: new Set(),
          titles: [],
        };
      }
      const g = by[a];
      g.sessions += 1;
      g.outTok += outputTokens(r) || 0;
      g.inTok += inputTokens(r) || 0;
      if (typeof r.runtime_seconds === "number") g.timeSec += r.runtime_seconds;
      if (r.model) g.models.add(r.model);
      const title = (r.title || "").slice(0, 90);
      if (title && g.titles.length < 40) g.titles.push(title);
    }
    return Object.values(by).sort((a, b) => b.timeSec - a.timeSec || b.outTok - a.outTok);
  }

  function aggregateByModel(rows) {
    // Always prefer model slices so card totals == KPI when filtering by model.
    // Fall back to sessions only if slices are missing entirely.
    const slices = rows.filter(
      (r) =>
        (r.source === "chakra_model" || r.source === "pi_model") && r.model
    );
    const pool = slices.length
      ? slices
      : rows.filter(
          (r) =>
            r.model &&
            (r.source === "chakra_session" || r.source === "pi_session")
        );
    const by = {};
    for (const r of pool) {
      const m = r.model || "unknown";
      const key = `${agentOf(r)}::${m}`;
      if (!by[key]) {
        by[key] = {
          model: m,
          agent: agentOf(r),
          prompts: 0,
          outTok: 0,
          inTok: 0,
          timeSec: 0,
          titles: [],
        };
      }
      const g = by[key];
      g.prompts += 1;
      g.outTok += outputTokens(r) || 0;
      g.inTok += inputTokens(r) || 0;
      if (typeof r.runtime_seconds === "number") g.timeSec += r.runtime_seconds;
      const title = (r.title || "").replace(/\s·\s[\w.\-]+$/, "").slice(0, 90);
      if (title && g.titles.length < 40) g.titles.push(title);
    }
    return Object.values(by).sort((a, b) => b.outTok - a.outTok || b.timeSec - a.timeSec);
  }

  function renderAgentCards(allRows) {
    const el = $("agentCards");
    if (!el) return;
    const groups = aggregateByAgent(allRows);
    if (!groups.length) {
      el.innerHTML =
        `<div class="model-card"><p class="sub">No agent sessions yet. Click <b>Full refresh</b> after Chakra/Pi runs.</p></div>`;
      return;
    }
    el.innerHTML = groups
      .map((g) => {
        const lis = g.titles.map((t) => `<li>${escapeHtml(t)}</li>`).join("");
        return `<div class="model-card">
          <h3><span class="agent-pill ${g.agent}">${escapeHtml(g.agent)}</span></h3>
          <div class="stats">
            <div><span>Sessions</span><br/><b>${g.sessions}</b></div>
            <div><span>Out tokens</span><br/><b>${fmtTokens(g.outTok)}</b></div>
            <div><span>In tokens</span><br/><b>${fmtTokens(g.inTok)}</b></div>
            <div><span>Time</span><br/><b>${fmtTime(g.timeSec)}</b></div>
            <div><span>Models</span><br/><b>${g.models.size}</b></div>
          </div>
          <ul>${lis || "<li class='muted'>No titles</li>"}</ul>
        </div>`;
      })
      .join("");
  }

  function renderModelCards(allRows) {
    const el = $("modelCards");
    if (!el) return;
    const groups = aggregateByModel(allRows);
    if (!groups.length) {
      el.innerHTML =
        `<div class="model-card"><p class="sub">No model-tagged sessions yet. Click <b>Sync now</b> / <b>Full refresh</b> after runs.</p></div>`;
      return;
    }
    el.innerHTML = groups
      .map((g) => {
        const lis = g.titles.map((t) => `<li>${escapeHtml(t)}</li>`).join("");
        return `<div class="model-card">
          <h3>${escapeHtml(g.model)} <span class="agent-pill ${g.agent}">${escapeHtml(g.agent)}</span></h3>
          <div class="stats">
            <div><span>Prompts/tasks</span><br/><b>${g.prompts}</b></div>
            <div><span>Out tokens</span><br/><b>${fmtTokens(g.outTok)}</b></div>
            <div><span>In tokens</span><br/><b>${fmtTokens(g.inTok)}</b></div>
            <div><span>Time</span><br/><b>${fmtTime(g.timeSec)}</b></div>
          </div>
          <ul>${lis || "<li class='muted'>No titles</li>"}</ul>
        </div>`;
      })
      .join("");
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function countBy(rows, keyFn) {
    const m = {};
    for (const r of rows) {
      const k = keyFn(r) || "—";
      m[k] = (m[k] || 0) + 1;
    }
    return m;
  }

  function renderCharts(rows) {
    destroyCharts();
    chartDefaults();
    const chartPool = tokenStatRows(rows);
    const recent = [...chartPool].reverse().slice(-30);
    const labels = recent.map((r, i) => `${i + 1}`);

    state.charts.complexity = new Chart($("chartComplexity"), {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Complexity",
            data: recent.map((r) => r.complexity_score ?? 0),
            borderColor: "#2ec4b6",
            backgroundColor: "rgba(46,196,182,0.15)",
            fill: true,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { min: 0, max: 100 } },
      },
    });

    const bands = countBy(chartPool, (r) => r.complexity_band);
    state.charts.bands = new Chart($("chartBands"), {
      type: "doughnut",
      data: {
        labels: Object.keys(bands),
        datasets: [
          {
            data: Object.values(bands),
            backgroundColor: ["#3dcf8e", "#f0a202", "#ff9f68", "#e4572e", "#4ea8de"],
          },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });

    state.charts.tokens = new Chart($("chartTokens"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Input",
            data: recent.map((r) => inputTokens(r) ?? 0),
            backgroundColor: "#4ea8de",
          },
          {
            label: "Output",
            data: recent.map((r) => outputTokens(r) ?? 0),
            backgroundColor: "#f0a202",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: {
              callback: (v) => fmtTokens(v),
            },
          },
        },
      },
    });

    state.charts.time = new Chart($("chartTime"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Hours",
            data: recent.map((r) =>
              r.runtime_seconds != null ? Number(r.runtime_seconds) / 3600 : 0
            ),
            backgroundColor: "#e4572e",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            ticks: {
              callback: (v) => (v >= 1 ? `${v}h` : `${Math.round(v * 60)}m`),
            },
          },
        },
      },
    });

    if ($("chartAgent")) {
      const byAgent = countBy(chartPool, agentOf);
      state.charts.agent = new Chart($("chartAgent"), {
        type: "doughnut",
        data: {
          labels: Object.keys(byAgent),
          datasets: [
            {
              data: Object.values(byAgent),
              backgroundColor: ["#4ea8de", "#f0a202", "#7f9aa8", "#2ec4b6"],
            },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }

    const bySrc = countBy(rows, (r) => r.source);
    state.charts.source = new Chart($("chartSource"), {
      type: "bar",
      data: {
        labels: Object.keys(bySrc),
        datasets: [{ data: Object.values(bySrc), backgroundColor: "#2ec4b6" }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
      },
    });

    const byCat = countBy(chartPool, (r) => r.category || "uncategorized");
    state.charts.category = new Chart($("chartCategory"), {
      type: "bar",
      data: {
        labels: Object.keys(byCat),
        datasets: [{ data: Object.values(byCat), backgroundColor: "#4ea8de" }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
      },
    });

    const modelGroups = aggregateByModel(rows);
    const mLabels = modelGroups.map((g) => `${g.model} (${g.agent})`);
    if ($("chartModelTokens")) {
      state.charts.modelTokens = new Chart($("chartModelTokens"), {
        type: "bar",
        data: {
          labels: mLabels,
          datasets: [
            {
              label: "Output tokens",
              data: modelGroups.map((g) => g.outTok),
              backgroundColor: "#2ec4b6",
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
        },
      });
    }
    if ($("chartModelTime")) {
      state.charts.modelTime = new Chart($("chartModelTime"), {
        type: "bar",
        data: {
          labels: mLabels,
          datasets: [
            {
              label: "Seconds",
              data: modelGroups.map((g) => Math.round(g.timeSec)),
              backgroundColor: "#f0a202",
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
        },
      });
    }
  }

  function fillSourceFilter(rows) {
    const sel = $("filterSource");
    const cur = sel.value;
    const sources = [...new Set(rows.map((r) => r.source).filter(Boolean))].sort();
    sel.innerHTML =
      `<option value="">All</option>` +
      sources.map((s) => `<option value="${s}">${s}</option>`).join("");
    sel.value = cur;
  }

  function fillModelFilter(rows) {
    const sel = $("filterModel");
    if (!sel) return;
    const cur = sel.value;
    const models = [
      ...new Set(
        rows
          .map((r) => r.model)
          .filter((m) => typeof m === "string" && m.trim() && m !== "<synthetic>")
          .map((m) => m.trim())
      ),
    ].sort((a, b) => a.localeCompare(b));
    sel.innerHTML =
      `<option value="">All</option>` +
      models.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
    if (cur && models.includes(cur)) sel.value = cur;
    else sel.value = "";
  }

  function paint() {
    const rows = filtered();
    renderKpis(rows);
    renderTable(rows);
    renderCharts(rows);
    renderAgentCards(state.records);
    renderModelCards(state.records);
  }

  async function loadRecords() {
    const res = await fetch("/api/records", { cache: "no-store" });
    const data = await res.json();
    state.records = data.records || [];
    fillSourceFilter(state.records);
    const modelRows = state.records.filter(
      (r) =>
        r.model &&
        (r.source === "chakra_session" ||
          r.source === "chakra_model" ||
          r.source === "chakra_history" ||
          r.source === "pi_session" ||
          r.source === "pi_model" ||
          r.source === "pipeline")
    );
    fillModelFilter(modelRows.length ? modelRows : state.records);
    paint();
  }

  async function sync(full = false) {
    $("syncStatus").textContent = full ? "full refresh…" : "syncing…";
    try {
      const res = await fetch(full ? "/api/refresh" : "/api/sync", {
        method: "POST",
        cache: "no-store",
      });
      const data = await res.json();
      await loadRecords();
      if (state.page === "usage" || state.page === "tasks") await loadUsage();
      if (state.page === "kimi3") await loadKimi();
      if (state.page === "dimensions") await loadDimensions();
      const n = data.total_records ?? state.records.length;
      const pi = data.synced_pi_sessions != null ? ` · pi ${data.synced_pi_sessions}` : "";
      const ch = data.synced_chakra_sessions != null ? ` · chakra ${data.synced_chakra_sessions}` : "";
      $("syncStatus").textContent = `live · ${n} records${ch}${pi} · ${new Date().toLocaleTimeString()}`;
    } catch (err) {
      $("syncStatus").textContent = "sync failed — is server running?";
      console.error(err);
    }
  }

  $("btnSync").onclick = () => sync(false);
  $("btnRefresh").onclick = () => sync(true);
  if ($("filterAgent")) $("filterAgent").onchange = paint;
  $("filterSource").onchange = paint;
  if ($("filterModel")) $("filterModel").onchange = paint;
  $("filterBand").onchange = paint;
  $("filterQ").oninput = paint;

  loadRecords()
    .then(() => {
      $("syncStatus").textContent = `live · ${state.records.length} records · loading sync…`;
      return sync(false);
    })
    .catch(() => {
      $("syncStatus").textContent = "ledger load failed — is server running?";
    })
    .finally(() => {
      setInterval(() => sync(false), state.pollMs);
    });


  /* ---- Usage / Kimi3 / Dimensions tabs (additive) ---- */
  function destroyChart(key) {
    if (state.charts[key]) {
      state.charts[key].destroy();
      delete state.charts[key];
    }
  }

  function setPage(page) {
    state.page = page;
    document.querySelectorAll(".page").forEach((el) => {
      el.classList.toggle("active", el.id === `page-${page}`);
    });
    document.querySelectorAll("#navTabs button").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.page === page);
    });
    if (page === "ledger") paint();
    if (page === "usage" || page === "tasks") loadUsage();
    if (page === "kimi3") loadKimi();
    if (page === "dimensions") loadDimensions();
  }

  function usageQuery() {
    const since = $("usageSince")?.value || "2026-08-13";
    const agent = $("usageAgent")?.value || "";
    const model = $("usageModel")?.value || "";
    const q = new URLSearchParams({ since });
    if (agent) q.set("agent", agent);
    if (model) q.set("model", model);
    return q.toString();
  }

  async function loadUsage() {
    try {
      const res = await fetch(`/api/usage?${usageQuery()}`, { cache: "no-store" });
      if (!res.ok) throw new Error(`usage HTTP ${res.status}`);
      state.usage = await res.json();
      fillUsageModelFilter(state.usage.models || []);
      renderUsage();
      renderTasks();
    } catch (err) {
      console.error(err);
      if ($("usageKpis")) {
        $("usageKpis").innerHTML =
          `<div class="kpi warn"><div class="label">Usage API</div><div class="value">ERR</div><div class="hint">${escapeHtml(String(err.message || err))}</div></div>`;
      }
    }
  }

  async function loadKimi() {
    const since = $("kimiSince")?.value || "2026-08-13";
    try {
      const res = await fetch(`/api/kimi3?since=${encodeURIComponent(since)}`, { cache: "no-store" });
      state.kimi = await res.json();
      renderKimi();
    } catch (err) {
      console.error(err);
    }
  }

  function fillUsageModelFilter(models) {
    const sel = $("usageModel");
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML =
      `<option value="">All</option>` +
      models.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
    if (cur && models.includes(cur)) sel.value = cur;
  }

  function renderUsage() {
    const d = state.usage;
    if (!d || !$("usageKpis")) return;
    if ($("usageNote")) $("usageNote").textContent = d.note || "";
    const cards = [
      { label: "Charged total", value: fmtTokens(d.charged_total, false), hint: "exact provider/Langfuse", cls: "good" },
      { label: "Charged in", value: fmtTokens(d.charged_input, false), hint: "billable input" },
      { label: "Charged out", value: fmtTokens(d.charged_output, false), hint: "billable output" },
      { label: "Estimate total", value: fmtTokens(d.est_total, true), hint: "NOT a bill", cls: "warn" },
      { label: "Wall time Σ", value: fmtTime(d.runtime_seconds), hint: "sessions only" },
      { label: "Exact rows", value: d.exact_rows ?? 0, hint: `pool=${d.pool_kind || "—"}` },
    ];
    $("usageKpis").innerHTML = cards
      .map((c) => `<div class="kpi ${c.cls || ""}"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></div>`)
      .join("");

    chartDefaults();
    try {
      destroyChart("usageDay");
      destroyChart("usageTime");
      const days = d.by_day || [];
      if ($("chartUsageDay")) {
        state.charts.usageDay = new Chart($("chartUsageDay"), {
          type: "bar",
          data: {
            labels: days.map((x) => x.day),
            datasets: [
              { label: "Charged", data: days.map((x) => x.charged_total || 0), backgroundColor: "#2ec4b6" },
              { label: "Estimate", data: days.map((x) => x.est_total || 0), backgroundColor: "#7f9aa8" },
            ],
          },
          options: { responsive: true, maintainAspectRatio: false, scales: { y: { ticks: { callback: (v) => fmtTokens(v) } } } },
        });
      }
      if ($("chartUsageTime")) {
        state.charts.usageTime = new Chart($("chartUsageTime"), {
          type: "bar",
          data: {
            labels: days.map((x) => x.day),
            datasets: [{ label: "Hours", data: days.map((x) => (x.runtime_seconds || 0) / 3600), backgroundColor: "#f0a202" }],
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
        });
      }
    } catch (err) {
      console.error("usage charts failed", err);
    }

    if ($("usageAgentCards")) {
      $("usageAgentCards").innerHTML = (d.by_agent || [])
        .map((g) => `<div class="model-card">
          <h3><span class="agent-pill ${escapeHtml(g.key)}">${escapeHtml(g.key)}</span></h3>
          <div class="stats">
            <div><span>Sessions</span><br/><b>${g.sessions}</b></div>
            <div><span>Charged</span><br/><b>${fmtTokens(g.charged_total)}</b></div>
            <div><span>Estimate</span><br/><b>${fmtTokens(g.est_total, true)}</b></div>
            <div><span>Time</span><br/><b>${fmtTime(g.runtime_seconds)}</b></div>
          </div>
        </div>`)
        .join("") || `<div class="model-card"><p class="sub">No agent usage rows in range.</p></div>`;
    }
    if ($("usageModelCards")) {
      $("usageModelCards").innerHTML = (d.by_model || [])
        .map((g) => {
          const [agent, model] = String(g.key).split("::");
          return `<div class="model-card">
            <h3>${escapeHtml(model || g.key)} <span class="agent-pill ${escapeHtml(agent || "other")}">${escapeHtml(agent || "")}</span></h3>
            <div class="stats">
              <div><span>Charged in</span><br/><b>${fmtTokens(g.charged_input)}</b></div>
              <div><span>Charged out</span><br/><b>${fmtTokens(g.charged_output)}</b></div>
              <div><span>Estimate</span><br/><b>${fmtTokens(g.est_total, true)}</b></div>
              <div><span>Time</span><br/><b>${fmtTime(g.runtime_seconds)}</b></div>
            </div>
          </div>`;
        })
        .join("") || `<div class="model-card"><p class="sub">No model usage in range.</p></div>`;
    }
    if ($("usageTbody")) {
      $("usageTbody").innerHTML = (d.rows || [])
        .map((r) => {
          const badge = r.exact ? `<span class="band exact">exact</span>` : `<span class="band est">est</span>`;
          return `<tr>
            <td class="mono">${escapeHtml(r.when || "")}</td>
            <td><span class="agent-pill ${escapeHtml(r.agent || "other")}">${escapeHtml(r.agent || "")}</span></td>
            <td class="mono">${escapeHtml(r.model || "—")}</td>
            <td class="mono">${escapeHtml(r.task_key || "—")}</td>
            <td>${escapeHtml(r.source || "")} ${badge}</td>
            <td class="mono">${fmtTokens(r.charged_input)}</td>
            <td class="mono">${fmtTokens(r.charged_output)}</td>
            <td class="mono">${fmtTokens(r.charged_total)}</td>
            <td class="mono">${fmtTokens(r.est_total, true)}</td>
            <td class="mono">${fmtTime(r.runtime_seconds)}</td>
            <td class="title-cell">${escapeHtml((r.title || "").slice(0, 90))}</td>
          </tr>`;
        })
        .join("");
    }
  }

  function renderTasks() {
    const d = state.usage;
    if (!d || !$("taskTbody")) return;
    const tasks = d.by_task || [];
    const withCharge = tasks.filter((t) => (t.charged_total || 0) > 0).length;
    if ($("taskKpis")) {
      $("taskKpis").innerHTML = [
        { label: "Tasks attributed", value: tasks.length, hint: "from workdirs/sessions" },
        { label: "With charged usage", value: withCharge, hint: "exact > 0" },
        { label: "Task time Σ", value: fmtTime(tasks.reduce((a, t) => a + (t.runtime_seconds || 0), 0)), hint: "attributed sessions" },
      ]
        .map((c) => `<div class="kpi"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></div>`)
        .join("");
    }
    $("taskTbody").innerHTML = tasks
      .map((t) => {
        const st = t.status || "—";
        return `<tr>
          <td class="mono">${escapeHtml(t.last_when || "")}</td>
          <td class="mono">${escapeHtml(t.task_key)}</td>
          <td><span class="band ${escapeHtml(st)}">${escapeHtml(st)}</span></td>
          <td class="mono">${escapeHtml(t.model || "—")}</td>
          <td class="mono">${fmtTokens(t.charged_input)}</td>
          <td class="mono">${fmtTokens(t.charged_output)}</td>
          <td class="mono">${fmtTokens(t.charged_total)}</td>
          <td class="mono">${fmtTokens(t.est_input, true)}</td>
          <td class="mono">${fmtTokens(t.est_output, true)}</td>
          <td class="mono">${fmtTime(t.runtime_seconds)}</td>
          <td class="mono">${t.runs ?? "—"}</td>
          <td class="title-cell">${escapeHtml((t.title || "").slice(0, 90))}</td>
        </tr>`;
      })
      .join("");
  }

  function renderKimi() {
    const d = state.kimi;
    if (!d || !$("kimiKpis")) return;
    $("kimiKpis").innerHTML = [
      { label: "Charged total", value: fmtTokens(d.charged_total, false), hint: "exact only", cls: "good" },
      { label: "Charged in", value: fmtTokens(d.charged_input, false), hint: "billable" },
      { label: "Charged out", value: fmtTokens(d.charged_output, false), hint: "billable" },
      { label: "Estimate total", value: fmtTokens(d.est_total, true), hint: "NOT a bill", cls: "warn" },
      { label: "Wall time", value: fmtTime(d.runtime_seconds), hint: "kimi sessions" },
      { label: "Exact rows", value: d.exact_rows ?? 0, hint: d.pool_kind || "" },
    ]
      .map((c) => `<div class="kpi ${c.cls || ""}"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></div>`)
      .join("");
    if ($("kimiMeta")) $("kimiMeta").textContent = d.note || d.provider_note || "";
    chartDefaults();
    destroyChart("kimiDay");
    destroyChart("kimiTasks");
    const days = d.by_day || [];
    if ($("chartKimiDay")) {
      state.charts.kimiDay = new Chart($("chartKimiDay"), {
        type: "bar",
        data: {
          labels: days.map((x) => x.day),
          datasets: [
            { label: "Charged", data: days.map((x) => x.charged_total || 0), backgroundColor: "#2ec4b6" },
            { label: "Estimate", data: days.map((x) => x.est_total || 0), backgroundColor: "#7f9aa8" },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { ticks: { callback: (v) => fmtTokens(v) } } } },
      });
    }
    const tasks = (d.by_task || []).slice(0, 12);
    if ($("chartKimiTasks")) {
      state.charts.kimiTasks = new Chart($("chartKimiTasks"), {
        type: "bar",
        data: {
          labels: tasks.map((t) => t.task_key),
          datasets: [{ label: "Est Σ", data: tasks.map((t) => t.est_total || 0), backgroundColor: "#f0a202" }],
        },
        options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
      });
    }
    $("kimiTbody").innerHTML = (d.by_task || [])
      .map((t) => `<tr>
          <td class="mono">${escapeHtml(t.last_when || "")}</td>
          <td class="mono">${escapeHtml(t.task_key)}</td>
          <td class="mono">${escapeHtml(t.model || "—")}</td>
          <td class="mono">${fmtTokens(t.charged_total)}</td>
          <td class="mono">${fmtTokens(t.est_input, true)}</td>
          <td class="mono">${fmtTokens(t.est_output, true)}</td>
          <td class="mono">${fmtTokens(t.est_total, true)}</td>
          <td class="mono">${fmtTime(t.runtime_seconds)}</td>
          <td class="title-cell">${escapeHtml((t.title || "").slice(0, 90))}</td>
        </tr>`)
      .join("");
  }

  async function loadDimensions() {
    try {
      const res = await fetch("/api/dimensions", { cache: "no-store" });
      state.dims = await res.json();
      fillDimFilters();
      renderDimensions();
    } catch (err) {
      console.error(err);
    }
  }

  function fillDimFilters() {
    const items = state.dims?.items || [];
    const fill = (id, values) => {
      const sel = $(id);
      if (!sel) return;
      const cur = sel.value;
      const opts = [...new Set(values.filter(Boolean))].sort();
      sel.innerHTML =
        `<option value="">All</option>` +
        opts.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
      if (cur && opts.includes(cur)) sel.value = cur;
    };
    fill("dimCategory", items.map((x) => x.category));
    fill("dimLang", items.map((x) => x.dimensions?.language_runtime));
    fill("dimUi", items.map((x) => x.dimensions?.ui_surface));
    fill("dimCx", items.map((x) => x.dimensions?.complexity));
    fill("dimStatus", items.map((x) => x.status));
  }

  function filteredDims() {
    const items = state.dims?.items || [];
    const cat = $("dimCategory")?.value || "";
    const lang = $("dimLang")?.value || "";
    const ui = $("dimUi")?.value || "";
    const cx = $("dimCx")?.value || "";
    const st = $("dimStatus")?.value || "";
    const q = ($("dimQ")?.value || "").trim().toLowerCase();
    return items.filter((it) => {
      const d = it.dimensions || {};
      if (cat && it.category !== cat) return false;
      if (lang && d.language_runtime !== lang) return false;
      if (ui && d.ui_surface !== ui) return false;
      if (cx && d.complexity !== cx) return false;
      if (st && it.status !== st) return false;
      if (q && !`${it.task_key} ${it.title}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }

  function renderDimensions() {
    if (!state.dims || !$("dimKpis")) return;
    const items = filteredDims();
    const sc = state.dims.status_counts || {};
    $("dimKpis").innerHTML = [
      { label: "Tasks", value: items.length, hint: `of ${state.dims.count || 0}` },
      { label: "Done", value: sc.done || 0, hint: "checkpoint" },
      { label: "Failed", value: sc.failed || 0, hint: "checkpoint" },
      { label: "Pending", value: (sc.not_started || 0) + (sc.running || 0), hint: "" },
    ]
      .map((c) => `<div class="kpi"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></div>`)
      .join("");

    chartDefaults();
    const mk = (key, canvasId, obj) => {
      destroyChart(key);
      if (!$(canvasId)) return;
      state.charts[key] = new Chart($(canvasId), {
        type: "doughnut",
        data: {
          labels: Object.keys(obj || {}),
          datasets: [{ data: Object.values(obj || {}), backgroundColor: ["#2ec4b6", "#4ea8de", "#f0a202", "#e4572e", "#7f9aa8", "#ff9f68"] }],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    };
    mk("dimLang", "chartDimLang", state.dims.language_counts);
    mk("dimCx", "chartDimCx", state.dims.complexity_counts);
    mk("dimUi", "chartDimUi", state.dims.ui_counts);
    mk("dimStatus", "chartDimStatus", state.dims.status_counts);

    const skip = new Set(["language_runtime", "ui_surface", "persistence", "complexity", "user_persona"]);
    $("dimTbody").innerHTML = items
      .map((it) => {
        const d = it.dimensions || {};
        const chips = Object.entries(d)
          .filter(([k, v]) => v != null && v !== "" && !skip.has(k))
          .slice(0, 6)
          .map(([k, v]) => `${k}=${v}`)
          .join(", ");
        const st = it.status || "not_started";
        return `<tr>
          <td class="mono">${escapeHtml(it.task_key)}</td>
          <td><span class="band ${st}">${escapeHtml(st)}</span></td>
          <td class="mono">${escapeHtml(d.language_runtime || "—")}</td>
          <td class="mono">${escapeHtml(d.ui_surface || "—")}</td>
          <td class="mono">${escapeHtml(d.persistence || "—")}</td>
          <td><span class="band ${escapeHtml(d.complexity || "low")}">${escapeHtml(d.complexity || "—")}</span></td>
          <td>${escapeHtml(d.user_persona || "—")}</td>
          <td class="mono">${escapeHtml(chips || "—")}</td>
          <td class="title-cell">${escapeHtml((it.title || "").slice(0, 90))}</td>
        </tr>`;
      })
      .join("");
  }

  document.querySelectorAll("#navTabs button").forEach((btn) => {
    btn.onclick = () => setPage(btn.dataset.page);
  });
  $("btnUsageReload") && ($("btnUsageReload").onclick = () => loadUsage());
  $("usageSince") && ($("usageSince").onchange = () => loadUsage());
  $("usageAgent") && ($("usageAgent").onchange = () => loadUsage());
  $("usageModel") && ($("usageModel").onchange = () => loadUsage());
  $("btnKimiReload") && ($("btnKimiReload").onclick = () => loadKimi());
  $("kimiSince") && ($("kimiSince").onchange = () => loadKimi());
  $("btnDimReload") && ($("btnDimReload").onclick = () => loadDimensions());
  ["dimCategory", "dimLang", "dimUi", "dimCx", "dimStatus"].forEach((id) => {
    if ($(id)) $(id).onchange = () => renderDimensions();
  });
  if ($("dimQ")) $("dimQ").oninput = () => renderDimensions();

})();
