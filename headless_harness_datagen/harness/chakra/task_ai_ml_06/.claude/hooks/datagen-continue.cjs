#!/usr/bin/env node
/**
 * Auto-continue Stop hook for gpt-oss datagen sessions (.cjs required).
 *
 * Chakra/this Claude build's Stop schema ONLY accepts:
 *   continue, suppressOutput, stopReason, decision(approve|block), reason, systemMessage
 * It does NOT accept hookSpecificOutput.additionalContext on Stop (validation fails → no continue).
 *
 * So we must use decision:"block" + reason. UI may say "Stop hook error" — that is the
 * continue signal, not a crash. suppressOutput hides stdout noise.
 */
const fs = require("fs");
const path = require("path");

const MAX_AUTO = Number(process.env.DATAGEN_CONTINUE_MAX || 120);
const DONE_RE = /\bDONE\b[\s:_-]*task[_\s]?\d+/i;
const DONE_TASK_10_RE = /\bDONE\b[\s:_-]*task[_\s]?10\b/i;

function findChakraRoot(start) {
  let dir = path.resolve(start || process.cwd());
  for (let i = 0; i < 12; i++) {
    const settings = path.join(dir, ".claude", "settings.json");
    if (fs.existsSync(settings) || fs.existsSync(path.join(dir, ".claude", "hooks", "datagen-continue.cjs"))) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return path.resolve(__dirname, "..", "..");
}

const ROOT = findChakraRoot(process.cwd());
const STATE = path.join(ROOT, ".claude", "datagen-continue.state.json");

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
  });
}

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE, "utf8"));
  } catch {
    return { count: 0 };
  }
}

function saveState(s) {
  fs.mkdirSync(path.dirname(STATE), { recursive: true });
  fs.writeFileSync(STATE, JSON.stringify(s));
}

function clearState() {
  try {
    fs.unlinkSync(STATE);
  } catch {
    /* ok */
  }
}

function lastAssistantText(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return "";
  const lines = fs.readFileSync(transcriptPath, "utf8").split(/\r?\n/).filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i--) {
    try {
      const row = JSON.parse(lines[i]);
      const role = row.role || row.message?.role;
      if (role !== "assistant") continue;
      const content = row.message?.content || row.content;
      if (typeof content === "string") return content;
      if (Array.isArray(content)) {
        const parts = content.filter((c) => c?.type === "text").map((c) => c.text || "");
        if (parts.length) return parts.join("\n");
      }
    } catch {
      /* skip */
    }
  }
  return "";
}

function emitContinue(reason) {
  process.stdout.write(
    JSON.stringify({
      decision: "block",
      reason,
      suppressOutput: true,
    })
  );
  process.exit(0);
}

async function main() {
  const raw = await readStdin();
  let input = {};
  try {
    input = JSON.parse(raw.replace(/^\uFEFF/, "").trim() || "{}");
  } catch {
    process.exit(0);
  }

  const status = input.status || input.stop_reason || "completed";
  if (status === "error" || status === "aborted") process.exit(0);

  const last = lastAssistantText(input.transcript_path);

  if (DONE_RE.test(last)) {
    clearState();
    if (DONE_TASK_10_RE.test(last)) {
      process.exit(0); // allow stop — marathon finished
    }
    // Mid-marathon DONE → force next task
    emitContinue(
      "CONTINUE (not an error): previous task DONE. Immediately open the NEXT task's single platform_prompt.md only. Implement with tools until demoable, print DONE task_N, then continue. No questions. No plan-only. No whole forged-file load. No hung background shells."
    );
  }

  const state = loadState();
  state.count = (state.count || 0) + 1;
  if (state.count > MAX_AUTO) {
    clearState();
    process.exit(0);
  }
  saveState(state);

  emitContinue(
    `CONTINUE ${state.count}/${MAX_AUTO} (not an error): you stopped before DONE task_N. Call tools now; finish a working interactive demo; print DONE task_N: <title> — path + how to run; then open the next platform_prompt.md. Forbidden: ask user, plan-only, stub HTML DONE, hung npm/servers.`
  );
}

main().catch(() => process.exit(0));
