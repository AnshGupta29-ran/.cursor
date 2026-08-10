/* Tidewatch browser port — loads Chakra-generated StreamingAssets JSON. */
(() => {
  const CONTENT = "../Assets/StreamingAssets/Content";
  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const logEl = document.getElementById("log");
  const banner = document.getElementById("banner");

  const state = {
    towersData: null,
    enemiesData: null,
    difficulty: null,
    level: null,
    grid: [],
    w: 0,
    h: 0,
    cell: 40,
    salvage: 0,
    lantern: 0,
    waveIndex: 0,
    waveActive: false,
    spawnQueue: [],
    enemies: [],
    towers: [],
    selectedTowerId: null,
    path: [],
    tidePhases: [],
    tideIndex: 0,
    tideT: 0,
    phase: "Low",
    paused: false,
    speed: 1,
    over: false,
    won: false,
    time: 0,
  };

  function log(msg) {
    const line = document.createElement("div");
    line.textContent = msg;
    logEl.prepend(line);
  }

  function tile(ch) {
    return { ch, flooded: false };
  }

  function parseGrid(rows) {
    state.grid = rows.map((r) => [...r].map(tile));
    state.h = state.grid.length;
    state.w = state.grid[0].length;
    state.cell = Math.floor(Math.min(960 / state.w, 480 / state.h));
    canvas.width = state.w * state.cell;
    canvas.height = state.h * state.cell;
  }

  function findChars(ch) {
    const out = [];
    for (let y = 0; y < state.h; y++)
      for (let x = 0; x < state.w; x++)
        if (state.grid[y][x].ch === ch) out.push({ x, y });
    return out;
  }

  function isWalkable(x, y, moveClass) {
    if (x < 0 || y < 0 || x >= state.w || y >= state.h) return false;
    const t = state.grid[y][x];
    const ch = t.ch;
    if (ch === "#" || ch === ".") return false;
    if (ch === "B" || ch === "G" || ch === "C") return true;
    if (ch === "~") return moveClass === "Pelagic" || moveClass === "Amphibious";
    if (ch === "T") {
      // trench: dry at Low, flooded otherwise for pathing
      const dry = state.phase === "Low";
      if (dry) return moveClass === "Terrestrial" || moveClass === "Amphibious";
      return moveClass === "Pelagic" || moveClass === "Amphibious";
    }
    return false;
  }

  function bfs(start, goal, moveClass) {
    const key = (p) => `${p.x},${p.y}`;
    const q = [start];
    const prev = new Map([[key(start), null]]);
    const dirs = [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ];
    while (q.length) {
      const cur = q.shift();
      if (cur.x === goal.x && cur.y === goal.y) break;
      for (const [dx, dy] of dirs) {
        const n = { x: cur.x + dx, y: cur.y + dy };
        const k = key(n);
        if (prev.has(k)) continue;
        if (!isWalkable(n.x, n.y, moveClass) && !(n.x === goal.x && n.y === goal.y))
          continue;
        prev.set(k, cur);
        q.push(n);
      }
    }
    if (!prev.has(key(goal))) return [];
    const path = [];
    let cur = goal;
    while (cur) {
      path.push(cur);
      cur = prev.get(key(cur));
    }
    path.reverse();
    return path;
  }

  function defaultPath() {
    const gates = findChars("G");
    const bases = findChars("B");
    if (!gates.length || !bases.length) return [];
    return bfs(gates[0], bases[0], "Terrestrial");
  }

  function applyTideFlood() {
    const high = state.phase === "High" || state.phase === "Rising";
    for (let y = 0; y < state.h; y++) {
      for (let x = 0; x < state.w; x++) {
        const t = state.grid[y][x];
        if (t.ch === "T" || t.ch === "C") t.flooded = high && t.ch === "T";
        if (t.ch === "~") t.flooded = true;
      }
    }
    // repath living enemies
    for (const e of state.enemies) {
      const base = findChars("B")[0];
      const path = bfs(
        { x: Math.round(e.x), y: Math.round(e.y) },
        base,
        e.moveClass
      );
      if (path.length) {
        e.path = path;
        e.pi = 0;
      }
      // Beached: pelagic on dry trench/causeway at Low
      e.beached =
        e.moveClass === "Pelagic" &&
        state.phase === "Low" &&
        state.grid[Math.round(e.y)]?.[Math.round(e.x)]?.ch === "T";
    }
    state.path = defaultPath();
  }

  function enemyDef(id) {
    return state.enemiesData.enemies.find((e) => e.id === id);
  }

  function towerDef(id) {
    return state.towersData.towers.find((t) => t.id === id);
  }

  function startWave() {
    if (state.over || state.waveActive) return;
    if (state.waveIndex >= state.level.waves.length) {
      state.won = true;
      state.over = true;
      log("Victory — Lantern held till dawn.");
      return;
    }
    const wave = state.level.waves[state.waveIndex];
    state.spawnQueue = [];
    for (const entry of wave.entries) {
      for (let i = 0; i < entry.count; i++) {
        state.spawnQueue.push({
          enemyId: entry.enemyId,
          at: state.time + (entry.delay || 0) + i * (entry.interval || 0.5),
        });
      }
    }
    state.spawnQueue.sort((a, b) => a.at - b.at);
    state.waveActive = true;
    log(`Wave ${state.waveIndex + 1} called.`);
  }

  function spawnEnemy(id) {
    const def = enemyDef(id);
    const gate = findChars("G")[0];
    const base = findChars("B")[0];
    const path = bfs(gate, base, def.moveClass);
    const hp =
      def.baseHp *
      state.difficulty.enemyHpMult;
    state.enemies.push({
      id,
      def,
      hp,
      maxHp: hp,
      x: gate.x,
      y: gate.y,
      moveClass: def.moveClass,
      path,
      pi: 0,
      shrouded: !!def.shrouded,
      beached: false,
      speed: def.baseSpeed * state.difficulty.enemySpeedMult,
    });
  }

  function dist(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.hypot(dx, dy);
  }

  function illuminated(ex, ey) {
    const base = findChars("B")[0];
    if (dist({ x: ex, y: ey }, base) <= 2.2) return true;
    for (const t of state.towers) {
      const def = towerDef(t.id);
      const tier = def.tiers[t.tier];
      if (!def.emitsLight) continue;
      if (dist(t, { x: ex, y: ey }) <= (tier.illuminationRadius || 3)) return true;
    }
    return false;
  }

  function update(dt) {
    if (state.paused || state.over) return;
    dt *= state.speed;
    state.time += dt;

    // tide
    const phase = state.tidePhases[state.tideIndex];
    state.tideT += dt;
    const dur = phase.seconds * state.difficulty.tideCadenceMult;
    const remain = dur - state.tideT;
    banner.classList.toggle("show", remain < 5 && remain > 0);
    if (state.tideT >= dur) {
      state.tideT = 0;
      state.tideIndex = (state.tideIndex + 1) % state.tidePhases.length;
      state.phase = state.tidePhases[state.tideIndex].phase;
      applyTideFlood();
      log(`Tide → ${state.phase}`);
    }

    // spawns
    while (state.spawnQueue.length && state.spawnQueue[0].at <= state.time) {
      spawnEnemy(state.spawnQueue.shift().enemyId);
    }
    if (state.waveActive && !state.spawnQueue.length && !state.enemies.length) {
      state.waveActive = false;
      const interest = Math.min(20, Math.floor(state.salvage * 0.04));
      state.salvage += 12 + interest;
      state.waveIndex += 1;
      log(`Wave cleared (+interest ${interest}).`);
      if (state.waveIndex >= state.level.waves.length) {
        state.won = true;
        state.over = true;
        log("Victory — all waves cleared.");
      }
    }

    // move enemies
    for (const e of state.enemies) {
      if (!e.path.length) continue;
      let spd = e.speed * (e.beached ? 0.45 : 1);
      let left = spd * dt;
      while (left > 0 && e.pi < e.path.length - 1) {
        const next = e.path[e.pi + 1];
        const dx = next.x - e.x;
        const dy = next.y - e.y;
        const d = Math.hypot(dx, dy) || 1e-6;
        const step = Math.min(left, d);
        e.x += (dx / d) * step;
        e.y += (dy / d) * step;
        left -= step;
        if (d - step <= 1e-4) e.pi += 1;
      }
      const base = findChars("B")[0];
      if (dist(e, base) < 0.35) {
        state.lantern -= e.def.leakDamage * state.difficulty.leakMult;
        log(`${e.def.displayName} leaked (−${e.def.leakDamage}).`);
        e.hp = 0;
      }
      e.shroudedActive = e.def.shrouded && !illuminated(e.x, e.y);
    }
    state.enemies = state.enemies.filter((e) => e.hp > 0);
    if (state.lantern <= 0) {
      state.lantern = 0;
      state.over = true;
      log("Defeat — the Lantern is extinguished.");
    }

    // towers fire
    for (const t of state.towers) {
      const def = towerDef(t.id);
      if (!def.dealsDamage) continue;
      const tier = def.tiers[t.tier];
      t.cd = (t.cd || 0) - dt;
      if (t.cd > 0) continue;
      let target = null;
      let best = 1e9;
      for (const e of state.enemies) {
        if (e.shroudedActive && def.directFire && !def.emitsLight) continue;
        const d = dist(t, e);
        if (d <= tier.range && d < best) {
          best = d;
          target = e;
        }
      }
      if (!target) continue;
      t.cd = 1 / (tier.fireRate || 1);
      let dmg = tier.damage;
      if (target.beached) dmg *= def.bonusVsBeached || 1;
      dmg = Math.max(1, dmg - target.def.armor);
      target.hp -= dmg;
      if (target.hp <= 0) {
        state.salvage += Math.floor(
          target.def.bounty * state.difficulty.bountyMult
        );
      }
    }
  }

  function colorFor(ch, flooded) {
    if (ch === "~") return "#163f63";
    if (ch === ".") return "#2a3540";
    if (ch === "C") return flooded ? "#2a5a78" : "#6b5a45";
    if (ch === "T") return flooded ? "#1a4a6e" : "#3a4a38";
    if (ch === "#") return "#3a6b4f";
    if (ch === "G") return "#8b3a3a";
    if (ch === "B") return "#c9a227";
    return "#111";
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const c = state.cell;
    for (let y = 0; y < state.h; y++) {
      for (let x = 0; x < state.w; x++) {
        const t = state.grid[y][x];
        ctx.fillStyle = colorFor(t.ch, t.flooded || state.phase === "High");
        ctx.fillRect(x * c, y * c, c - 1, c - 1);
        if (t.ch === "#") {
          ctx.strokeStyle = "#7dcaa5";
          ctx.strokeRect(x * c + 4, y * c + 4, c - 9, c - 9);
        }
      }
    }
    // path hint
    ctx.strokeStyle = "rgba(255,220,120,0.25)";
    ctx.beginPath();
    for (let i = 0; i < state.path.length; i++) {
      const p = state.path[i];
      const px = p.x * c + c / 2;
      const py = p.y * c + c / 2;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    for (const t of state.towers) {
      const def = towerDef(t.id);
      ctx.fillStyle = def.emitsLight ? "#ffe08a" : "#9ad0ff";
      ctx.beginPath();
      ctx.arc(t.x * c + c / 2, t.y * c + c / 2, c * 0.32, 0, Math.PI * 2);
      ctx.fill();
      if (def.emitsLight) {
        const r = (def.tiers[t.tier].illuminationRadius || 3) * c;
        ctx.strokeStyle = "rgba(255,220,100,0.25)";
        ctx.beginPath();
        ctx.arc(t.x * c + c / 2, t.y * c + c / 2, r, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    for (const e of state.enemies) {
      ctx.globalAlpha = e.shroudedActive ? 0.35 : 1;
      ctx.fillStyle = e.def.isBoss
        ? "#ff6b6b"
        : e.beached
          ? "#d4a017"
          : e.moveClass === "Pelagic"
            ? "#5ec8ff"
            : "#e8e8e8";
      ctx.beginPath();
      ctx.arc(e.x * c + c / 2, e.y * c + c / 2, c * 0.28, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
      // hp bar
      const pct = Math.max(0, e.hp / e.maxHp);
      ctx.fillStyle = "#222";
      ctx.fillRect(e.x * c + 4, e.y * c + 2, c - 8, 3);
      ctx.fillStyle = "#3d9a6a";
      ctx.fillRect(e.x * c + 4, e.y * c + 2, (c - 8) * pct, 3);
    }

    if (state.over) {
      ctx.fillStyle = "rgba(0,0,0,0.55)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = state.won ? "#7dcaa5" : "#ff8a7a";
      ctx.font = "bold 28px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText(
        state.won ? "VICTORY" : "DEFEAT",
        canvas.width / 2,
        canvas.height / 2
      );
    }

    document.getElementById("salvage").textContent = state.salvage;
    document.getElementById("lantern").textContent = Math.ceil(state.lantern);
    document.getElementById("wave").textContent = `${Math.min(
      state.waveIndex + 1,
      state.level.waves.length
    )}/${state.level.waves.length}`;
    document.getElementById("tidePhase").textContent = state.phase;
    const phase = state.tidePhases[state.tideIndex];
    const dur = phase.seconds * state.difficulty.tideCadenceMult;
    document.getElementById("tideBar").style.width = `${Math.min(
      100,
      (state.tideT / dur) * 100
    )}%`;
    document.getElementById("speedLabel").textContent = `${state.speed}×`;
  }

  function placeTower(gx, gy) {
    if (!state.selectedTowerId || state.over) return;
    const cell = state.grid[gy]?.[gx];
    if (!cell || cell.ch !== "#") {
      log("Build only on raised plots (#).");
      return;
    }
    if (state.towers.some((t) => t.x === gx && t.y === gy)) {
      log("Plot occupied.");
      return;
    }
    const def = towerDef(state.selectedTowerId);
    const cost = def.tiers[0].cost;
    if (state.salvage < cost) {
      log("Not enough Salvage.");
      return;
    }
    state.salvage -= cost;
    state.towers.push({
      id: def.id,
      x: gx,
      y: gy,
      tier: 0,
      cd: 0,
    });
    log(`Built ${def.displayName} (−${cost}).`);
  }

  canvas.addEventListener("click", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const sx = canvas.width / rect.width;
    const sy = canvas.height / rect.height;
    const x = Math.floor(((ev.clientX - rect.left) * sx) / state.cell);
    const y = Math.floor(((ev.clientY - rect.top) * sy) / state.cell);
    placeTower(x, y);
  });

  document.getElementById("btnWave").onclick = startWave;
  document.getElementById("btnSpeed").onclick = () => {
    state.speed = state.speed === 1 ? 2 : 1;
  };
  document.getElementById("btnPause").onclick = () => {
    state.paused = !state.paused;
  };
  document.getElementById("btnRestart").onclick = () => location.reload();

  window.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
      e.preventDefault();
      startWave();
    }
    if (e.key === "Escape") state.selectedTowerId = null;
    const map = ["1", "2", "3", "4", "5"];
    if (map.includes(e.key) && state.towersData) {
      const t = state.towersData.towers[Number(e.key) - 1];
      if (t) selectTower(t.id);
    }
  });

  function selectTower(id) {
    state.selectedTowerId = id;
    document.querySelectorAll(".tower-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.id === id);
    });
  }

  function buildTowerButtons() {
    const root = document.getElementById("towers");
    root.innerHTML = "";
    state.towersData.towers.forEach((t, i) => {
      const btn = document.createElement("button");
      btn.className = "tower-btn";
      btn.dataset.id = t.id;
      btn.innerHTML = `<strong>${i + 1}. ${t.displayName}</strong><small>${t.tiers[0].cost} Salvage · range ${t.tiers[0].range}</small>`;
      btn.onclick = () => selectTower(t.id);
      root.appendChild(btn);
    });
  }

  async function load() {
    const [towers, enemies, difficulties, level] = await Promise.all([
      fetch(`${CONTENT}/towers.json`).then((r) => r.json()),
      fetch(`${CONTENT}/enemies.json`).then((r) => r.json()),
      fetch(`${CONTENT}/difficulties.json`).then((r) => r.json()),
      fetch(`${CONTENT}/Levels/level_01.json`).then((r) => r.json()),
    ]);
    state.towersData = towers;
    state.enemiesData = enemies;
    state.difficulty = difficulties.difficulties[0];
    state.level = level;
    state.salvage = state.difficulty.startingSalvage;
    state.lantern = state.difficulty.lanternLight;
    state.tidePhases = level.tideSchedule;
    state.phase = level.tideSchedule[0].phase;
    parseGrid(level.grid);
    // Some generated levels omit explicit B — treat the rightmost C on a gate row as base.
    if (!findChars("B").length) {
      for (let y = 0; y < state.h; y++) {
        for (let x = state.w - 1; x >= 0; x--) {
          if (state.grid[y][x].ch === "C") {
            state.grid[y][x].ch = "B";
            break;
          }
        }
        if (findChars("B").length) break;
      }
    }
    if (!findChars("G").length) {
      for (let y = 0; y < state.h; y++) {
        for (let x = 0; x < state.w; x++) {
          if (state.grid[y][x].ch === "C") {
            state.grid[y][x].ch = "G";
            break;
          }
        }
        if (findChars("G").length) break;
      }
    }
    applyTideFlood();
    buildTowerButtons();
    selectTower(towers.towers[0].id);
    log("Tidewatch ready. Build on green plots, then Call wave.");
  }

  let last = performance.now();
  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  load()
    .then(() => requestAnimationFrame(loop))
    .catch((err) => {
      log("Failed to load content JSON: " + err.message);
      console.error(err);
    });
})();
