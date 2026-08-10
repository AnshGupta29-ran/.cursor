/**
 * Tracks thinking capture state across hook invocations (stateless processes).
 * Pending reasoning from preToolUse is flushed at stop if afterAgentThought never fired.
 */

import {
  readFileSync,
  writeFileSync,
  appendFileSync,
  existsSync,
  mkdirSync,
  unlinkSync,
} from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { createHash } from "crypto";

const STATE_DIR = join(tmpdir(), "cursor-langfuse-hooks", "thinking-state");

function ensureDir() {
  if (!existsSync(STATE_DIR)) {
    mkdirSync(STATE_DIR, { recursive: true });
  }
}

function capturedPath(generationId) {
  return join(STATE_DIR, `${generationId}.captured`);
}

function pendingPath(generationId) {
  return join(STATE_DIR, `${generationId}.pending.jsonl`);
}

export function thinkingObservationId(generationId, text) {
  const hash = createHash("sha256")
    .update(String(text).substring(0, 2000))
    .digest("hex")
    .substring(0, 16);
  return `${generationId}-thinking-${hash}`;
}

export function markThinkingCaptured(generationId) {
  if (!generationId) return;
  try {
    ensureDir();
    writeFileSync(capturedPath(generationId), Date.now().toString());
  } catch {
    // fail open — don't block hooks
  }
}

export function hasThinkingCaptured(generationId) {
  if (!generationId) return false;
  try {
    return existsSync(capturedPath(generationId));
  } catch {
    return false;
  }
}

export function queuePendingReasoning(generationId, entry) {
  if (!generationId || !entry?.text?.trim()) return;
  try {
    ensureDir();
    appendFileSync(pendingPath(generationId), `${JSON.stringify(entry)}\n`);
  } catch {
    // fail open
  }
}

export function consumePendingReasoning(generationId) {
  if (!generationId) return [];
  try {
    const path = pendingPath(generationId);
    if (!existsSync(path)) return [];

    const lines = readFileSync(path, "utf8")
      .trim()
      .split("\n")
      .filter(Boolean);

    unlinkSync(path);
    return lines.map((line) => JSON.parse(line));
  } catch {
    return [];
  }
}

export function cleanupGenerationState(generationId) {
  if (!generationId) return;
  try {
    for (const path of [capturedPath(generationId), pendingPath(generationId)]) {
      if (existsSync(path)) unlinkSync(path);
    }
  } catch {
    // fail open
  }
}

/**
 * Extract thinking text from hook input (field names vary by Cursor version).
 */
export function extractThinkingText(input) {
  return input.text ?? input.thinking ?? input.thought ?? input.content ?? null;
}

/**
 * Heuristic: agent_message in preToolUse is reasoning, not hook denial text.
 */
export function looksLikeReasoning(message) {
  if (!message || message.length < 10) return false;
  const lower = message.toLowerCase();
  if (lower.includes("blocked by a hook")) return false;
  if (lower.includes("has been blocked")) return false;
  return true;
}
