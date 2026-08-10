/* Agent Prompt Analytics frontend (Chakra + Pi) */
(() => {
  const state = {
    records: [],
    charts: {},
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

    const cards = [
      { label: "Records", value: rows.length, hint: "matching filters (table rows)" },
      { label: "Agents", value: agents.size || "—", hint: [...agents].join(" · ") || "none in view" },
      { label: "Avg complexity", value: avg(scores)?.toFixed(1) ?? "—", hint: "0–100 score" },
      { label: "Avg output tok", value: fmtTokens(avg(outs), true), hint: model ? "per model slice" : "per session" },
      {
        label: "Total output tok Σ",
        value: fmtTokens(sumOut || null),
        hint: poolHint,
      },
      { label: "Avg time", value: fmtTime(avg(times)), hint: "wall clock" },
      {
        label: "Total time Σ",
        value: fmtTime(times.reduce((a, b) => a + b, 0) || null),
        hint: model ? "model-slice active spans" : "session wall clocks",
      },
      {
        label: "Max complexity",
        value: scores.length ? Math.max(...scores).toFixed(0) : "—",
        hint: "hardest prompt",
      },
    ];
    $("kpis").innerHTML = cards
      .map(
        (c) =>
          `<div class="kpi"><div class="label">${c.label}</div><div class="value">${c.value}</div><div class="hint">${c.hint}</div></div>`
      )
      .join("");
  }

  function renderTable(rows) {
    $("tbody").innerHTML = rows
      .map((r) => {
        const band = r.complexity_band || "low";
        const est = isTokEst(r);
        const agent = agentOf(r);
        return `<tr>
          <td class="mono">${(whenOf(r) || "").slice(0, 19)}</td>
          <td><span class="agent-pill ${agent}">${escapeHtml(agent)}</span></td>
          <td class="mono">${escapeHtml(r.model || "—")}</td>
          <td>${r.source || "—"}</td>
          <td>${escapeHtml(r.category || "—")}</td>
          <td><span class="band ${band}">${band}</span></td>
          <td class="mono">${r.complexity_score != null ? Number(r.complexity_score).toFixed(1) : "—"}</td>
          <td class="mono">${fmtTokens(inputTokens(r), est)}</td>
          <td class="mono">${fmtTokens(outputTokens(r), est)}</td>
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
})();
