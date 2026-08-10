#!/usr/bin/env node
/**
 * Auto-continue Stop hook for gpt-oss datagen sessions.
 * Must be .cjs — package.json may have "type": "module".
 * Resolves chakra project root by walking up from cwd (survives cd into task folders).
 */
const fs = require("fs");
const path = require("path");

const MAX_AUTO = Number(process.env.DATAGEN_CONTINUE_MAX || 60);
const DONE_RE = /\bDONE\b[\s:_-]*(task[_\s]?\d+)?/i;

function findChakraRoot(start) {
  let dir = path.resolve(start || process.cwd());
  for (let i = 0; i < 12; i++) {
    const hook = path.join(dir, ".claude", "hooks", "datagen-continue.cjs");
    const settings = path.join(dir, ".claude", "settings.json");
    if (fs.existsSync(hook) || fs.existsSync(settings)) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  // Fallback: directory containing this script's ../../
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

function lastAssistantText(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return "";
  const lines = fs.readFileSync(transcriptPath, "utf8").split(/\r?\n/).filter(Boolean);
  let text = "";
  for (let i = lines.length - 1; i >= 0; i--) {
    try {
      const row = JSON.parse(lines[i]);
      const role = row.role || row.message?.role;
      if (role !== "assistant") continue;
      const content = row.message?.content || row.content;
      if (typeof content === "string") {
        text = content;
        break;
      }
      if (Array.isArray(content)) {
        const parts = content.filter((c) => c?.type === "text").map((c) => c.text || "");
        if (parts.length) {
          text = parts.join("\n");
          break;
        }
      }
    } catch {
      /* skip */
    }
  }
  return text;
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
    try {
      fs.unlinkSync(STATE);
    } catch {
      /* ok */
    }
    process.exit(0);
  }

  const state = loadState();
  state.count = (state.count || 0) + 1;
  if (state.count > MAX_AUTO) {
    process.stderr.write(
      `[datagen-continue] max auto-continues (${MAX_AUTO}) reached — stopping.\n`
    );
    try {
      fs.unlinkSync(STATE);
    } catch {
      /* ok */
    }
    process.exit(0);
  }
  saveState(state);

  const reason = [
    `AUTO-CONTINUE ${state.count}/${MAX_AUTO}: You stopped mid-task without printing DONE.`,
    "Do not ask for confirmation. Do not plan-only. Immediately call tools and keep implementing until the acceptance criteria pass, then print DONE.",
    "Ignore any urge to wait for the user.",
  ].join(" ");

  process.stdout.write(
    JSON.stringify({
      decision: "block",
      reason,
      systemMessage: `Datagen auto-continue ${state.count}/${MAX_AUTO}`,
    })
  );
  process.exit(0);
}

main().catch(() => process.exit(0));
