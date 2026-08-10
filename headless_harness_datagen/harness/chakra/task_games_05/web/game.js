/* Frostborne Clash — browser canvas card battler */
(() => {
  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const $ = (id) => document.getElementById(id);

  const CARDS = [
    { id: "c001", name: "Frost Warrior", cost: 2, type: "Creature", atk: 3, hp: 3, color: "#6ec6ff" },
    { id: "c002", name: "Ice Blast", cost: 3, type: "Spell", dmg: 4, color: "#9ad5f0" },
    { id: "c003", name: "Glacial Shield", cost: 1, type: "Artifact", shield: 3, color: "#7fd4c2" },
    { id: "c004", name: "Snow Stalker", cost: 1, type: "Creature", atk: 2, hp: 1, color: "#b8e0f0" },
    { id: "c005", name: "Ice Construct", cost: 4, type: "Creature", atk: 4, hp: 5, color: "#4ec3e0" },
    { id: "c006", name: "Blizzard", cost: 5, type: "Spell", dmg: 2, aoe: true, color: "#d0ecff" },
    { id: "c007", name: "Crystal Pike", cost: 2, type: "Creature", atk: 4, hp: 2, color: "#8fd3ff" },
    { id: "c008", name: "Permafrost", cost: 2, type: "Artifact", buffAtk: 1, color: "#a8fff0" },
  ];

  const COLS = 6;
  const ROWS = 5;
  const TURN_SEC = 30;

  const state = {
    turn: "you",
    turnLeft: TURN_SEC,
    frostline: 0,
    selected: null,
    you: { hp: 30, mana: 3, maxMana: 3, shield: 0, atkBuff: 0, hand: [], deck: [], board: [] },
    ai: { hp: 30, mana: 3, maxMana: 3, shield: 0, atkBuff: 0, hand: [], deck: [], board: [] },
    log: "Your turn — play cards onto your half of the board.",
    over: null,
    pulse: 0,
  };

  function shuffle(a) {
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function freshDeck() {
    const d = [];
    for (let i = 0; i < 4; i++) for (const c of CARDS) d.push({ ...c, uid: `${c.id}-${i}-${Math.random().toString(36).slice(2, 7)}` });
    return shuffle(d);
  }

  function drawTo(p, n = 1) {
    for (let i = 0; i < n; i++) {
      if (!p.deck.length) p.deck = freshDeck();
      if (p.hand.length >= 7) break;
      p.hand.push(p.deck.pop());
    }
  }

  function reset() {
    state.turn = "you";
    state.turnLeft = TURN_SEC;
    state.frostline = 0;
    state.selected = null;
    state.over = null;
    state.you = { hp: 30, mana: 3, maxMana: 3, shield: 0, atkBuff: 0, hand: [], deck: freshDeck(), board: [] };
    state.ai = { hp: 30, mana: 3, maxMana: 3, shield: 0, atkBuff: 0, hand: [], deck: freshDeck(), board: [] };
    drawTo(state.you, 5);
    drawTo(state.ai, 5);
    state.log = "Frostborne Clash — click a card, then an open cell on your side.";
    tickHud();
  }

  function usableCols() {
    return Math.max(2, COLS - state.frostline);
  }

  function layout() {
    const W = canvas.width;
    const H = canvas.height;
    const boardY = 56;
    const boardH = H - 220;
    const cellW = (W - 40) / COLS;
    const cellH = boardH / ROWS;
    return { W, H, boardY, boardH, cellW, cellH, handY: H - 150 };
  }

  function cellAt(x, y) {
    const L = layout();
    const gx = x - 20;
    const gy = y - L.boardY;
    if (gx < 0 || gy < 0) return null;
    const c = Math.floor(gx / L.cellW);
    const r = Math.floor(gy / L.cellH);
    if (c < 0 || c >= usableCols() || r < 0 || r >= ROWS) return null;
    return { c, r };
  }

  function handHit(x, y) {
    const L = layout();
    if (y < L.handY) return null;
    const n = state.you.hand.length;
    if (!n) return null;
    const cardW = 108;
    const gap = 10;
    const total = n * cardW + (n - 1) * gap;
    let sx = (L.W - total) / 2;
    for (let i = 0; i < n; i++) {
      const cx = sx + i * (cardW + gap);
      if (x >= cx && x <= cx + cardW && y >= L.handY && y <= L.handY + 130) return i;
    }
    return null;
  }

  function unitAt(owner, c, r) {
    return owner.board.find((u) => u.c === c && u.r === r);
  }

  function dealDamage(target, amount) {
    let dmg = amount;
    if (target.shield > 0) {
      const soak = Math.min(target.shield, dmg);
      target.shield -= soak;
      dmg -= soak;
    }
    target.hp -= dmg;
  }

  function playCard(player, card, cell, isYou) {
    if (player.mana < card.cost) {
      state.log = `Need ${card.cost} mana.`;
      return false;
    }
    if (card.type === "Creature") {
      if (!cell) return false;
      const sideOk = isYou ? cell.r >= 3 : cell.r <= 1;
      if (!sideOk) {
        state.log = isYou ? "Place creatures on your rows (bottom)." : "AI misplace";
        return false;
      }
      if (unitAt(state.you, cell.c, cell.r) || unitAt(state.ai, cell.c, cell.r)) {
        state.log = "Cell occupied.";
        return false;
      }
      player.mana -= card.cost;
      player.board.push({
        ...card,
        c: cell.c,
        r: cell.r,
        hp: card.hp,
        atk: card.atk + (player.atkBuff || 0),
      });
      state.log = `Played ${card.name} at (${cell.c},${cell.r}).`;
    } else if (card.type === "Spell") {
      player.mana -= card.cost;
      const foe = isYou ? state.ai : state.you;
      if (card.aoe) {
        for (const u of [...foe.board]) {
          u.hp -= card.dmg;
        }
        foe.board = foe.board.filter((u) => u.hp > 0);
        dealDamage(foe, Math.ceil(card.dmg / 2));
        state.log = `${card.name} lashes the board for ${card.dmg}.`;
      } else {
        // hit lowest-hp enemy unit or face
        const sorted = [...foe.board].sort((a, b) => a.hp - b.hp);
        if (sorted.length) {
          sorted[0].hp -= card.dmg;
          foe.board = foe.board.filter((u) => u.hp > 0);
          state.log = `${card.name} hits ${sorted[0].name} for ${card.dmg}.`;
        } else {
          dealDamage(foe, card.dmg);
          state.log = `${card.name} hits face for ${card.dmg}.`;
        }
      }
    } else if (card.type === "Artifact") {
      player.mana -= card.cost;
      if (card.shield) player.shield += card.shield;
      if (card.buffAtk) {
        player.atkBuff += card.buffAtk;
        for (const u of player.board) u.atk += card.buffAtk;
      }
      state.log = `Activated ${card.name}.`;
    }
    player.hand = player.hand.filter((c) => c.uid !== card.uid);
    checkOver();
    return true;
  }

  function combat(attacker, defender) {
    for (const u of attacker.board) {
      // attack opposite column if enemy present, else face
      const foes = defender.board.filter((e) => e.c === u.c);
      if (foes.length) {
        const t = foes[0];
        t.hp -= u.atk;
        u.hp -= Math.max(1, Math.floor(t.atk / 2));
      } else {
        dealDamage(defender, u.atk);
      }
    }
    attacker.board = attacker.board.filter((u) => u.hp > 0);
    defender.board = defender.board.filter((u) => u.hp > 0);
  }

  function checkOver() {
    if (state.you.hp <= 0) state.over = "AI wins — the glacier claims you.";
    if (state.ai.hp <= 0) state.over = "Victory — Frostborne Clash!";
  }

  function crystallize() {
    if (state.turn !== "you" || state.over) return;
    if (state.you.mana <= 0) {
      state.log = "No mana to crystallize.";
      return;
    }
    const spent = state.you.mana;
    state.you.mana = 0;
    state.you.atkBuff += 1;
    for (const u of state.you.board) u.atk += 1;
    state.log = `Crystallized ${spent} mana → +1 ATK buff.`;
    tickHud();
  }

  function endYourTurn() {
    if (state.turn !== "you" || state.over) return;
    combat(state.you, state.ai);
    checkOver();
    if (state.over) {
      tickHud();
      return;
    }
    // frostline every 2 full rounds (after your turn count)
    advanceToAi();
  }

  function advanceToAi() {
    state.turn = "ai";
    state.turnLeft = TURN_SEC;
    state.selected = null;
    state.ai.maxMana = Math.min(10, state.ai.maxMana + 1);
    state.ai.mana = state.ai.maxMana;
    drawTo(state.ai, 1);
    state.log = "AI thinking…";
    tickHud();
    setTimeout(aiTurn, 450);
  }

  function aiTurn() {
    if (state.over) return;
    // play affordable cards greedily
    const plays = [...state.ai.hand].sort((a, b) => b.cost - a.cost);
    for (const card of plays) {
      if (state.ai.mana < card.cost) continue;
      if (card.type === "Creature") {
        let placed = false;
        for (let r = 0; r <= 1 && !placed; r++) {
          for (let c = 0; c < usableCols() && !placed; c++) {
            if (!unitAt(state.you, c, r) && !unitAt(state.ai, c, r)) {
              playCard(state.ai, card, { c, r }, false);
              placed = true;
            }
          }
        }
      } else {
        playCard(state.ai, card, null, false);
      }
    }
    combat(state.ai, state.you);
    checkOver();
    // frostline advance every AI turn end (pressure)
    state.frostline = Math.min(COLS - 2, state.frostline + (state.frostline % 2 === 1 ? 1 : 0));
    // simpler: advance every other turn based on maxMana
    if (state.you.maxMana % 2 === 0) {
      state.frostline = Math.min(COLS - 2, state.frostline + 1);
      // purge units outside
      const lim = usableCols();
      state.you.board = state.you.board.filter((u) => u.c < lim);
      state.ai.board = state.ai.board.filter((u) => u.c < lim);
      state.log = `Frostline advances — board width ${lim}.`;
    }
    if (state.over) {
      tickHud();
      return;
    }
    state.turn = "you";
    state.turnLeft = TURN_SEC;
    state.you.maxMana = Math.min(10, state.you.maxMana + 1);
    state.you.mana = state.you.maxMana;
    drawTo(state.you, 1);
    if (!state.log.includes("Frostline")) state.log = "Your turn.";
    tickHud();
  }

  function tickHud() {
    $("youHud").textContent = `You HP ${Math.max(0, state.you.hp)} · Mana ${state.you.mana}/${state.you.maxMana}` +
      (state.you.shield ? ` · Shield ${state.you.shield}` : "") +
      (state.you.atkBuff ? ` · ATK+${state.you.atkBuff}` : "");
    $("aiHud").textContent = `AI HP ${Math.max(0, state.ai.hp)} · Mana ${state.ai.mana}/${state.ai.maxMana}`;
    $("timerHud").textContent = state.over ? "Done" : `${state.turn === "you" ? "Your" : "AI"} ${Math.ceil(state.turnLeft)}s`;
    $("frostHud").textContent = `Frostline ${state.frostline} · cols ${usableCols()}`;
    $("log").textContent = state.over || state.log;
    $("btnEnd").disabled = state.turn !== "you" || !!state.over;
    $("btnCrystal").disabled = state.turn !== "you" || !!state.over || state.you.mana <= 0;
  }

  function draw() {
    const L = layout();
    ctx.clearRect(0, 0, L.W, L.H);
    // title strip
    ctx.fillStyle = "#0d2130";
    ctx.fillRect(0, 0, L.W, 48);
    ctx.fillStyle = "#9ad5f0";
    ctx.font = "600 16px IBM Plex Sans";
    ctx.fillText(state.over || (state.turn === "you" ? "Your deployment" : "AI turn"), 20, 30);

    // board
    const lim = usableCols();
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const x = 20 + c * L.cellW;
        const y = L.boardY + r * L.cellH;
        const frozen = c >= lim;
        ctx.fillStyle = frozen ? "#15202a" : r >= 3 ? "#123040" : r <= 1 ? "#1a2838" : "#0f2230";
        ctx.fillRect(x + 2, y + 2, L.cellW - 4, L.cellH - 4);
        ctx.strokeStyle = frozen ? "#2a3340" : "#2a5160";
        ctx.strokeRect(x + 2, y + 2, L.cellW - 4, L.cellH - 4);
        if (frozen) {
          ctx.fillStyle = "rgba(150,180,200,0.08)";
          ctx.fillRect(x + 2, y + 2, L.cellW - 4, L.cellH - 4);
        }
      }
    }
    // mid line
    ctx.strokeStyle = "#4ec3e0";
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(20, L.boardY + L.cellH * 2.5);
    ctx.lineTo(20 + lim * L.cellW, L.boardY + L.cellH * 2.5);
    ctx.stroke();
    ctx.setLineDash([]);

    function drawUnit(u, mine) {
      const x = 20 + u.c * L.cellW + 6;
      const y = L.boardY + u.r * L.cellH + 6;
      const w = L.cellW - 12;
      const h = L.cellH - 12;
      ctx.fillStyle = u.color || (mine ? "#2a6a80" : "#6a3a40");
      roundRect(x, y, w, h, 8, true);
      ctx.fillStyle = "#0b1520";
      ctx.font = "600 12px IBM Plex Sans";
      ctx.fillText(u.name.slice(0, 12), x + 8, y + 18);
      ctx.font = "500 13px IBM Plex Mono";
      ctx.fillText(`${u.atk}/${u.hp}`, x + 8, y + h - 10);
    }
    for (const u of state.ai.board) drawUnit(u, false);
    for (const u of state.you.board) drawUnit(u, true);

    // hand
    ctx.fillStyle = "#0d1c28";
    ctx.fillRect(0, L.handY - 8, L.W, 160);
    ctx.fillStyle = "#7f9aa8";
    ctx.font = "12px IBM Plex Sans";
    ctx.fillText("Hand", 20, L.handY - 14);
    const n = state.you.hand.length;
    const cardW = 108;
    const cardH = 130;
    const gap = 10;
    const total = n * cardW + (n - 1) * gap;
    let sx = (L.W - total) / 2;
    state.you.hand.forEach((card, i) => {
      const x = sx + i * (cardW + gap);
      const y = L.handY;
      const sel = state.selected === i;
      const afford = state.you.mana >= card.cost && state.turn === "you" && !state.over;
      ctx.fillStyle = sel ? "#1e5a4a" : afford ? "#183848" : "#121c24";
      roundRect(x, y, cardW, cardH, 10, true);
      ctx.strokeStyle = sel ? "#f0c14b" : card.color || "#4ec3e0";
      ctx.lineWidth = sel ? 3 : 1.5;
      roundRect(x, y, cardW, cardH, 10, false);
      ctx.lineWidth = 1;
      ctx.fillStyle = "#e8f2f6";
      ctx.font = "600 12px IBM Plex Sans";
      wrapText(card.name, x + 8, y + 22, cardW - 16, 14);
      ctx.fillStyle = "#9ad5f0";
      ctx.font = "11px IBM Plex Mono";
      ctx.fillText(`${card.type} · ${card.cost}◆`, x + 8, y + 58);
      ctx.fillStyle = "#c8d8e0";
      ctx.font = "11px IBM Plex Sans";
      const detail =
        card.type === "Creature"
          ? `${card.atk}/${card.hp}`
          : card.type === "Spell"
            ? `DMG ${card.dmg}${card.aoe ? " AoE" : ""}`
            : card.shield
              ? `Shield +${card.shield}`
              : `ATK +${card.buffAtk}`;
      ctx.fillText(detail, x + 8, y + 110);
    });

    if (state.over) {
      ctx.fillStyle = "rgba(8,16,24,0.72)";
      ctx.fillRect(0, 0, L.W, L.H);
      ctx.fillStyle = "#f0c14b";
      ctx.font = "700 28px IBM Plex Sans";
      ctx.textAlign = "center";
      ctx.fillText(state.over, L.W / 2, L.H / 2);
      ctx.textAlign = "left";
    }
  }

  function roundRect(x, y, w, h, r, fill) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
    if (fill) ctx.fill();
    else ctx.stroke();
  }

  function wrapText(text, x, y, maxW, lineH) {
    const words = text.split(" ");
    let line = "";
    let yy = y;
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width > maxW && line) {
        ctx.fillText(line, x, yy);
        line = w;
        yy += lineH;
      } else line = test;
    }
    ctx.fillText(line, x, yy);
  }

  canvas.addEventListener("click", (ev) => {
    if (state.over || state.turn !== "you") return;
    const rect = canvas.getBoundingClientRect();
    const x = ((ev.clientX - rect.left) / rect.width) * canvas.width;
    const y = ((ev.clientY - rect.top) / rect.height) * canvas.height;
    const hi = handHit(x, y);
    if (hi != null) {
      state.selected = state.selected === hi ? null : hi;
      state.log = `Selected ${state.you.hand[hi].name}. Click a board cell (or cast).`;
      const card = state.you.hand[hi];
      if (card.type !== "Creature") {
        // instant cast
        if (playCard(state.you, card, null, true)) state.selected = null;
      }
      tickHud();
      return;
    }
    if (state.selected == null) return;
    const card = state.you.hand[state.selected];
    const cell = cellAt(x, y);
    if (card.type === "Creature") {
      if (playCard(state.you, card, cell, true)) state.selected = null;
    }
    tickHud();
  });

  $("btnEnd").onclick = endYourTurn;
  $("btnCrystal").onclick = crystallize;
  $("btnRestart").onclick = reset;

  let last = performance.now();
  function loop(now) {
    const dt = (now - last) / 1000;
    last = now;
    state.pulse = (state.pulse + dt) % 1;
    if (!state.over && state.turn === "you") {
      state.turnLeft -= dt;
      if (state.turnLeft <= 0) {
        state.log = "Turn timer expired.";
        endYourTurn();
      }
    }
    tickHud();
    draw();
    requestAnimationFrame(loop);
  }

  reset();
  requestAnimationFrame(loop);
})();
