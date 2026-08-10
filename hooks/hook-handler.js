#!/usr/bin/env node

/**
 * Cursor Hooks Langfuse Integration
 *
 * Session  = conversation_id + environment (one Cursor chat)
 * Trace    = generation_id (one agent turn)
 */

import { readStdin } from "./lib/utils.js";
import {
  getOrCreateTrace,
  flushLangfuse,
  HOOK_HANDLER_VERSION,
  NO_TRACE_HOOKS,
  hookLog,
  testLangfuseClientConfig,
  resolveSessionId,
  resolveConversationId,
} from "./lib/langfuse-client.js";
import { routeHookHandler } from "./lib/handlers.js";

function safeAllow() {
  console.log(JSON.stringify({ continue: true, permission: "allow" }));
}

async function main() {
  try {
    const input = await readStdin();
    const hookName = input.hook_event_name || "unknown";

    if (NO_TRACE_HOOKS.has(hookName)) {
      const response = routeHookHandler(hookName, null, input);
      console.log(JSON.stringify(response ?? { permission: "allow" }));
      return;
    }

    const cfg = testLangfuseClientConfig();
    if (!cfg.hasSecretKey || !cfg.hasPublicKey) {
      hookLog("missing credentials — allowing without ingest", {
        hook: hookName,
        baseUrl: cfg.baseUrl,
      });
      const response = routeHookHandler(hookName, null, input);
      if (response !== null && response !== undefined) {
        console.log(JSON.stringify(response));
      } else {
        safeAllow();
      }
      return;
    }

    const sessionId = resolveSessionId(input);
    const conversationId = resolveConversationId(input);
    const trace = getOrCreateTrace(input);
    const response = routeHookHandler(hookName, trace, input);

    if (response !== null && response !== undefined) {
      console.log(JSON.stringify(response));
    }

    await flushLangfuse();
    hookLog("ingested", {
      hook: hookName,
      environment: cfg.environment,
      session_id: sessionId,
      conversation_id: conversationId,
      generation_id: input.generation_id || null,
    });
  } catch (error) {
    hookLog(`Error: ${error.message}`);
    safeAllow();
    process.exit(0);
  }
}

main();
