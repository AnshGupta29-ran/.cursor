let currentId = null;
let currentScores = null;

const $ = (id) => document.getElementById(id);

function showError(msg) {
  $("error").textContent = msg || "";
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) {
    const msg = data?.detail?.message || data?.detail || res.statusText;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

function drawRadar(radar) {
  const c = $("radar");
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  const keys = Object.keys(radar || {});
  const n = keys.length || 1;
  const cx = c.width / 2, cy = c.height / 2, R = 100;
  ctx.strokeStyle = "#c9d5cc";
  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const a = (-Math.PI / 2) + (i % n) * (2 * Math.PI / n);
      const r = (R * ring) / 4;
      const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath(); ctx.stroke();
  }
  function poly(field, color) {
    ctx.beginPath();
    keys.forEach((k, i) => {
      const a = (-Math.PI / 2) + i * (2 * Math.PI / n);
      const v = radar[k][field] || 0;
      const x = cx + R * v * Math.cos(a), y = cy + R * v * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.strokeStyle = color;
    ctx.stroke();
  }
  poly("jd_norm", "#2f5d50");
  poly("resume_norm", "#c45c26");
  ctx.fillStyle = "#13212b";
  ctx.font = "12px sans-serif";
  keys.forEach((k, i) => {
    const a = (-Math.PI / 2) + i * (2 * Math.PI / n);
    const x = cx + (R + 18) * Math.cos(a), y = cy + (R + 18) * Math.sin(a);
    ctx.fillText(k.split("/")[0], x - 20, y);
  });
}

function drawGauge(resumeBand, jdBand) {
  const order = ["IC3", "IC4", "IC5", "IC6", "IC7"];
  const c = $("gauge");
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  const y = 90, x0 = 40, x1 = c.width - 40;
  ctx.strokeStyle = "#2f5d50"; ctx.lineWidth = 8;
  ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
  order.forEach((b, i) => {
    const x = x0 + (i / (order.length - 1)) * (x1 - x0);
    ctx.fillStyle = "#13212b"; ctx.fillText(b, x - 10, y + 28);
    if (b === resumeBand) {
      ctx.fillStyle = "#c45c26"; ctx.beginPath(); ctx.arc(x, y, 10, 0, Math.PI * 2); ctx.fill();
      ctx.fillText("resume", x - 18, y - 18);
    }
    if (b === jdBand) {
      ctx.strokeStyle = "#2f5d50"; ctx.beginPath(); ctx.arc(x, y, 14, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = "#2f5d50"; ctx.fillText("JD", x - 8, y - 34);
    }
  });
}

function drawGaps(gaps) {
  const c = $("gaps");
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  const top = (gaps || []).slice(0, 6);
  top.forEach((g, i) => {
    const y = 30 + i * 30;
    const w = Math.max(40, 280 - i * 30);
    ctx.fillStyle = "#c45d2688";
    ctx.fillRect(80, y - 12, w, 18);
    ctx.fillStyle = "#13212b";
    ctx.fillText(g, 8, y);
  });
  if (!top.length) {
    ctx.fillStyle = "#5b6b73";
    ctx.fillText("No skill gaps vs JD lexicon", 20, 40);
  }
}

function render(data) {
  currentId = data.analysis_id;
  currentScores = data;
  $("dashboard").style.display = "block";
  $("matchScore").textContent = data.match_score;
  $("coverage").textContent = data.skill_coverage + "%";
  $("tfidf").textContent = data.tfidf_similarity + "%";
  $("rBand").textContent = `${data.seniority_band} (${data.seniority_score})`;
  $("jBand").textContent = `${data.jd_seniority_band} (${data.jd_seniority_score})`;
  $("recs").innerHTML = (data.recommendations || []).map((r) => `<li>${r}</li>`).join("") || "<li class=muted>None</li>";
  drawRadar(data.radar);
  drawGauge(data.seniority_band, data.jd_seniority_band);
  drawGaps(data.skill_gaps);
}

$("btnAnalyze").onclick = async () => {
  showError("");
  $("btnAnalyze").disabled = true;
  try {
    const jd = $("jdText").value;
    const title = $("jdTitle").value || "Target role";
    const file = $("file").files[0];
    let data;
    if (file) {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("jd_text", jd);
      fd.append("jd_title", title);
      data = await api("/api/analyze", { method: "POST", body: fd });
    } else {
      const fd = new FormData();
      fd.append("resume_text", $("resumeText").value);
      fd.append("jd_text", jd);
      fd.append("jd_title", title);
      data = await api("/api/analyze/text", { method: "POST", body: fd });
    }
    $("demoBanner").style.display = "none";
    render(data);
  } catch (e) {
    showError(e.message);
  } finally {
    $("btnAnalyze").disabled = false;
  }
};

$("btnDemo").onclick = async () => {
  showError("");
  $("btnDemo").disabled = true;
  try {
    const seeded = await api("/api/demo/seed", { method: "POST" });
    $("demoBanner").style.display = "block";
    // show strongest demo run
    const best = (seeded.seeded || []).slice().sort((a, b) => b.match_score - a.match_score)[0];
    if (best) {
      const detail = await api(`/api/analyses/${best.analysis_id}`);
      render({ analysis_id: best.analysis_id, ...detail.scores });
    }
  } catch (e) {
    showError(e.message);
  } finally {
    $("btnDemo").disabled = false;
  }
};

$("btnHistory").onclick = async () => {
  $("history").style.display = "block";
  const data = await api("/api/analyses");
  $("histBody").innerHTML = (data.analyses || []).map((a) =>
    `<tr><td>${a.id}</td><td>${a.filename}</td><td>${a.jd_title}</td><td>${a.match_score}</td><td>${a.seniority_band}</td><td>${a.mode}</td></tr>`
  ).join("");
};

$("btnExportJson").onclick = () => {
  if (!currentId) return;
  window.open(`/api/analyses/${currentId}/export?format=json`, "_blank");
};
$("btnExportCsv").onclick = () => {
  if (!currentId) return;
  window.open(`/api/analyses/${currentId}/export?format=csv`, "_blank");
};
