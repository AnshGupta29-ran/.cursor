/**
 * Langfuse Client Module
 *
 * Data model:
 * - Session  = one Cursor chat (conversation_id + environment)
 * - Trace    = one agent turn (generation_id)
 * - Tools    = child observations
 * - Generation = LLM output only
 */

import { Langfuse } from "langfuse";
import { config } from "dotenv";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";
import { appendFileSync, mkdirSync, existsSync } from "fs";
import {
  generateTraceName,
  generateSessionId,
  generateTraceTags,
  normalizeGenerationId,
} from "./utils.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const hooksRoot = resolve(__dirname, "..");
const logDir = join(hooksRoot, "logs");
const logFile = join(logDir, "langfuse-hooks.log");

function loadEnv() {
  const envCandidates = [
    resolve(hooksRoot, ".env", "Credentials.txt"),
    resolve(hooksRoot, ".env"),
    resolve(process.cwd(), ".env", "Credentials.txt"),
    resolve(process.cwd(), ".env"),
  ];

  for (const envPath of envCandidates) {
    config({ path: envPath });
    if (process.env.LANGFUSE_SECRET_KEY) break;
  }

  for (const key of [
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_BASE_URL",
    "LANGFUSE_ENVIRONMENT",
  ]) {
    if (typeof process.env[key] === "string") {
      process.env[key] = process.env[key].trim();
    }
  }
  if (process.env.LANGFUSE_BASE_URL) {
    process.env.LANGFUSE_BASE_URL = process.env.LANGFUSE_BASE_URL.replace(/\/+$/, "");
  }
}

loadEnv();

export const HOOK_HANDLER_VERSION = "1.5.1";

/** Hooks that only return allow/continue — no Langfuse network I/O. */
export const NO_TRACE_HOOKS = new Set([
  "beforeShellExecution",
  "beforeMCPExecution",
  "preToolUse",
]);

let langfuseInstance = null;
let initError = null;

export function getLangfuseEnvironment() {
  return process.env.LANGFUSE_ENVIRONMENT || "development";
}

export function hookLog(message, extra = null) {
  try {
    if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true });
    const line =
      `[${new Date().toISOString()}] ${message}` +
      (extra != null ? ` ${typeof extra === "string" ? extra : JSON.stringify(extra)}` : "") +
      "\n";
    appendFileSync(logFile, line);
  } catch {
    // never break the agent for logging
  }
  console.error(`[Langfuse Hook v${HOOK_HANDLER_VERSION}] ${message}`);
}

function assertConfigured() {
  if (!process.env.LANGFUSE_SECRET_KEY || !process.env.LANGFUSE_PUBLIC_KEY) {
    throw new Error(
      "Missing LANGFUSE_SECRET_KEY / LANGFUSE_PUBLIC_KEY (expected hooks/.env/Credentials.txt)"
    );
  }
}

export function getLangfuseClient() {
  if (initError) throw initError;
  if (!langfuseInstance) {
    try {
      assertConfigured();
      langfuseInstance = new Langfuse({
        secretKey: process.env.LANGFUSE_SECRET_KEY,
        publicKey: process.env.LANGFUSE_PUBLIC_KEY,
        baseUrl: process.env.LANGFUSE_BASE_URL || "https://cloud.langfuse.com",
        release: HOOK_HANDLER_VERSION,
        environment: getLangfuseEnvironment(),
        flushAt: 1,
        requestTimeout: 20_000,
      });
    } catch (err) {
      initError = err;
      hookLog(`init failed: ${err.message}`);
      throw err;
    }
  }
  return langfuseInstance;
}

export function testLangfuseClientConfig() {
  return {
    version: HOOK_HANDLER_VERSION,
    hasSecretKey: Boolean(process.env.LANGFUSE_SECRET_KEY),
    hasPublicKey: Boolean(process.env.LANGFUSE_PUBLIC_KEY),
    baseUrl: process.env.LANGFUSE_BASE_URL || "https://cloud.langfuse.com",
    environment: getLangfuseEnvironment(),
  };
}

export function resolveConversationId(input) {
  return input.conversation_id || input.session_id || null;
}

export function resolveSessionId(input) {
  return generateSessionId(resolveConversationId(input), getLangfuseEnvironment());
}

/**
 * Stable Langfuse trace id for one agent turn.
 * Collapses Cursor thinking suffixes onto the parent generation_id.
 */
export function resolveTraceId(input) {
  const normalized = normalizeGenerationId(input.generation_id);
  if (normalized) return normalized;

  const conversationId = resolveConversationId(input);
  if (conversationId && input.hook_event_name?.startsWith("session")) {
    return `cursor-session-${getLangfuseEnvironment()}-${conversationId}`.slice(0, 200);
  }
  if (conversationId) {
    return `cursor-${getLangfuseEnvironment()}-${conversationId}-turn`.slice(0, 200);
  }
  return `cursor-orphan-${Date.now()}`;
}

/**
 * Get or create the trace for the current agent turn.
 * Always attaches sessionId so Langfuse Sessions stay populated.
 */
export function getOrCreateTrace(input) {
  const langfuse = getLangfuseClient();
  const traceId = resolveTraceId(input);
  const conversationId = resolveConversationId(input);
  const sessionId = resolveSessionId(input);
  const environment = getLangfuseEnvironment();

  const body = {
    id: traceId,
    sessionId,
    userId: input.user_email || "cursor-user",
    release: HOOK_HANDLER_VERSION,
    version: input.cursor_version,
    metadata: {
      conversation_id: conversationId,
      generation_id: input.generation_id || null,
      generation_id_normalized: normalizeGenerationId(input.generation_id),
      cursor_version: input.cursor_version,
      model: input.model,
      workspace_roots: input.workspace_roots,
      hook_event: input.hook_event_name,
      hook_handler_version: HOOK_HANDLER_VERSION,
      langfuse_environment: environment,
      langfuse_session_id: sessionId,
    },
    tags: [...generateTraceTags(input), `env-${environment}`, "cursor-session"],
  };

  if (input.prompt) {
    body.name = generateTraceName(input.prompt, input.model);
  } else if (input.hook_event_name === "sessionStart") {
    body.name = `Cursor session ${String(conversationId || "").slice(0, 8) || "new"}`;
  }

  return langfuse.trace(body);
}

export function addScore(trace, name, value, comment = null, dataType = "NUMERIC") {
  if (trace) {
    trace.score({ name, value, comment, dataType });
  }
}

export function addCompletionScores(trace, input) {
  let statusScore = 0;
  let statusComment = "";

  switch (input.status) {
    case "completed":
      statusScore = 1;
      statusComment = "Agent completed successfully";
      break;
    case "aborted":
      statusScore = 0.5;
      statusComment = "Agent was aborted by user";
      break;
    case "error":
      statusScore = 0;
      statusComment = "Agent encountered an error";
      break;
    default:
      statusScore = 0.5;
      statusComment = `Unknown status: ${input.status}`;
  }

  addScore(trace, "completion_status", statusScore, statusComment);

  if (typeof input.loop_count === "number") {
    const efficiencyScore = Math.max(0, 1 - input.loop_count / 10);
    addScore(
      trace,
      "efficiency",
      efficiencyScore,
      `Completed in ${input.loop_count} loops`
    );
  }
}

export async function flushLangfuse() {
  const started = Date.now();
  try {
    await getLangfuseClient().flushAsync();
    hookLog(`flush ok ${Date.now() - started}ms`);
  } catch (err) {
    hookLog(`flush failed after ${Date.now() - started}ms: ${err.message}`);
    throw err;
  }
}

export async function shutdownLangfuse() {
  await getLangfuseClient().shutdownAsync();
}
