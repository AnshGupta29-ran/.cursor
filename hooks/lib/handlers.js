/**
 * Hook Handlers Module
 *
 * Langfuse trace tree per agent turn:
 *   Trace (input: prompt, output: response)
 *   ├── generation: agent-response
 *   ├── span: agent-thinking
 *   ├── tool: grep-search | read-file | shell-exec | edit-file | ...
 *   └── event: agent-stopped
 *
 * @see https://langfuse.com/faq/all/what-does-a-good-trace-look-like
 */

import {
  calculateEditStats,
  getFileExtension,
  determineLevel,
  parseToolOutput,
  generateTraceName,
} from "./utils.js";
import { addCompletionScores } from "./langfuse-client.js";
import { enrichGrepOutput } from "./grep-enricher.js";
import {
  toolName,
  toolDescription,
  recordTool,
  recordGeneration,
  recordThinking,
  flushPendingThinking,
  buildReadToolInput,
  buildReadToolOutput,
  buildShellToolInput,
  buildEditToolOutput,
} from "./tracing.js";
import {
  thinkingObservationId,
  markThinkingCaptured,
  hasThinkingCaptured,
  queuePendingReasoning,
  consumePendingReasoning,
  cleanupGenerationState,
  extractThinkingText,
  looksLikeReasoning,
} from "./thinking-state.js";

// Tools traced by dedicated lifecycle hooks — skip in postToolUse to avoid duplicates.
const DEDICATED_TOOL_HOOKS = new Set([
  "Read",
  "Shell",
  "Write",
  "StrReplace",
]);

function isDedicatedTool(toolName) {
  return DEDICATED_TOOL_HOOKS.has(toolName) || toolName?.startsWith("MCP:");
}

function formatObservationName(baseName, detail) {
  return detail ? `${baseName}: ${detail}` : baseName;
}

export function handleBeforeSubmitPrompt(trace, input) {
  const attachments = input.attachments?.map((a) => ({
    type: a.type,
    path: a.filePath,
    extension: getFileExtension(a.filePath),
  }));

  if (trace) {
    // Creating/updating this turn with sessionId is what materializes the
    // Langfuse Session for a Cursor chat (including brand-new chats).
    trace.update({
      name: generateTraceName(input.prompt, input.model),
      input: {
        prompt: input.prompt,
        source: "cursor",
        hook: "beforeSubmitPrompt",
      },
      metadata: {
        attachment_count: attachments?.length ?? 0,
        ...(attachments?.length > 0 && { attachments }),
        cursor_conversation_id: input.conversation_id || input.session_id,
      },
    });
    trace.event({
      name: "user-prompt",
      input: input.prompt,
      metadata: {
        model: input.model,
      },
    });
  }

  return { continue: true };
}

export function handleSessionStart(trace, input) {
  if (trace) {
    const conversationId = input.conversation_id || input.session_id || "new";
    trace.update({
      name: `Cursor session ${String(conversationId).slice(0, 8)}`,
      input: {
        event: "sessionStart",
        composer_mode: input.composer_mode,
        is_background_agent: input.is_background_agent,
        conversation_id: conversationId,
      },
      metadata: {
        cursor_conversation_id: conversationId,
        workspace_roots: input.workspace_roots,
      },
    });
    trace.event({
      name: "session-start",
      metadata: {
        composer_mode: input.composer_mode,
        cursor_version: input.cursor_version,
        conversation_id: conversationId,
      },
    });
  }
  return {};
}

export function handleSessionEnd(trace, input) {
  if (trace) {
    trace.event({
      name: "session-end",
      metadata: {
        reason: input.reason || input.status || "closed",
        session_id: input.session_id || input.conversation_id,
      },
    });
  }
  return {};
}

export function handleSubagentStart(trace, input) {
  if (trace) {
    trace.event({
      name: "subagent-start",
      metadata: {
        subagent_type: input.subagent_type,
        task: input.task,
        description: input.description,
      },
    });
  }
  return { permission: "allow" };
}

export function handleAfterAgentResponse(trace, input) {
  if (trace) {
    trace.update({ output: input.text });
  }

  recordGeneration(trace, {
    name: "agent-response",
    output: input.text,
    model: input.model,
    metadata: {
      response_length: input.text?.length ?? 0,
      line_count: input.text?.split("\n").length ?? 0,
    },
  });

  return null;
}

export function handleAfterAgentThought(trace, input) {
  const text = extractThinkingText(input);
  if (!text?.trim()) return null;

  const recorded = recordThinking(trace, {
    text,
    model: input.model,
    durationMs: input.duration_ms,
    source: "afterAgentThought",
    id: thinkingObservationId(input.generation_id, text),
  });

  if (recorded && input.generation_id) {
    markThinkingCaptured(input.generation_id);
    consumePendingReasoning(input.generation_id);
  }

  return null;
}

export function handlePreToolUse(_trace, input) {
  const agentMessage = input.agent_message?.trim();

  if (
    agentMessage &&
    input.generation_id &&
    looksLikeReasoning(agentMessage) &&
    !hasThinkingCaptured(input.generation_id)
  ) {
    queuePendingReasoning(input.generation_id, {
      text: agentMessage,
      source: "pre-tool-reasoning",
      model: input.model,
      id: thinkingObservationId(input.generation_id, agentMessage),
      metadata: {
        tool_name: input.tool_name,
        tool_use_id: input.tool_use_id,
      },
    });
  }

  return { permission: "allow" };
}

export function handleSubagentStop(trace, input) {
  const text = input.summary?.trim();
  if (!text) return null;

  recordThinking(trace, {
    text,
    model: input.subagent_model,
    durationMs: input.duration_ms,
    source: "subagent",
    id: thinkingObservationId(input.generation_id, `subagent-${text}`),
    metadata: {
      subagent_type: input.subagent_type,
      task: input.task,
      status: input.status,
      message_count: input.message_count,
      tool_call_count: input.tool_call_count,
    },
  });

  return null;
}

export function handleBeforeShellExecution(_trace, _input) {
  return { permission: "allow" };
}

export function handleAfterShellExecution(trace, input) {
  const outputLower = (input.output || "").toLowerCase();
  const mightHaveFailed =
    outputLower.includes("error") ||
    outputLower.includes("failed") ||
    outputLower.includes("not found");

  recordTool(trace, {
    name: formatObservationName("shell-exec", input.command?.substring(0, 60)),
    input: buildShellToolInput(input.command, input.cwd),
    output: input.output,
    durationMs: input.duration,
    level: mightHaveFailed ? "WARNING" : "DEFAULT",
    metadata: {
      output_length: input.output?.length ?? 0,
      might_have_failed: mightHaveFailed,
    },
  });

  return null;
}

export function handleBeforeMCPExecution(_trace, _input) {
  return { permission: "allow" };
}

export function handleAfterMCPExecution(trace, input) {
  let toolInput = input.tool_input;
  if (typeof toolInput === "string") {
    try {
      toolInput = JSON.parse(toolInput);
    } catch {
      toolInput = { raw: toolInput };
    }
  }

  recordTool(trace, {
    name: formatObservationName(
      toolName(`MCP:${input.tool_name}`, toolInput),
      input.tool_name
    ),
    input: { tool_name: input.tool_name, tool_input: toolInput },
    output: input.result_json,
    durationMs: input.duration,
  });

  return null;
}

export function handleBeforeReadFile(trace, input) {
  recordTool(trace, {
    name: formatObservationName(
      "read-file",
      input.file_path?.split("/").pop()
    ),
    input: buildReadToolInput(input.file_path, input.content),
    output: buildReadToolOutput(input.content),
    metadata: {
      file_extension: getFileExtension(input.file_path),
    },
  });

  return { permission: "allow" };
}

export function handleAfterFileEdit(trace, input) {
  const extension = getFileExtension(input.file_path);
  const editStats = calculateEditStats(input.edits);

  recordTool(trace, {
    name: formatObservationName("edit-file", input.file_path?.split("/").pop()),
    input: { file_path: input.file_path, extension },
    output: buildEditToolOutput(input.file_path, input.edits, editStats),
    metadata: { file_extension: extension, ...editStats },
  });

  return null;
}

export function handleStop(trace, input) {
  if (trace) {
    flushPendingThinking(
      trace,
      input.generation_id,
      consumePendingReasoning,
      hasThinkingCaptured,
      cleanupGenerationState
    );

    trace.event({
      name: "agent-stopped",
      level: determineLevel(input.status),
      metadata: {
        status: input.status,
        loop_count: input.loop_count,
      },
    });

    addCompletionScores(trace, input);
  }
  return {};
}

export function handleBeforeTabFileRead(trace, input) {
  recordTool(trace, {
    name: formatObservationName("read-file", input.file_path?.split("/").pop()),
    input: buildReadToolInput(input.file_path, input.content),
    output: buildReadToolOutput(input.content),
    metadata: {
      file_extension: getFileExtension(input.file_path),
      source: "tab",
    },
  });

  return { permission: "allow" };
}

export function handlePostToolUse(trace, input) {
  const name = input.tool_name || "Tool";

  if (isDedicatedTool(name)) {
    return null;
  }

  const parsedOutput = parseToolOutput(input.tool_output);
  const output =
    name === "Grep"
      ? enrichGrepOutput(parsedOutput, input.tool_input ?? {})
      : parsedOutput;

  const baseName = toolName(name, input.tool_input ?? {});
  const detail = toolDescription(name, input.tool_input ?? {});

  recordTool(trace, {
    name: formatObservationName(baseName, detail),
    input: input.tool_input,
    output,
    durationMs: input.duration,
    metadata: {
      tool_use_id: input.tool_use_id,
      ...(name === "Grep" && {
        output_mode: input.tool_input?.output_mode,
        file_count: output?.file_count,
        match_line_count: output?.match_line_count,
      }),
    },
  });

  return null;
}

export function handlePostToolUseFailure(trace, input) {
  const name = input.tool_name || "Tool";
  const baseName = toolName(name, input.tool_input ?? {});
  const detail = toolDescription(name, input.tool_input ?? {});

  recordTool(trace, {
    name: formatObservationName(baseName, detail),
    input: input.tool_input,
    output: { error: input.error_message },
    durationMs: input.duration,
    level: "ERROR",
    metadata: {
      tool_use_id: input.tool_use_id,
      failed: true,
    },
  });

  return null;
}

export function handleAfterTabFileEdit(trace, input) {
  const extension = getFileExtension(input.file_path);
  const editStats = calculateEditStats(input.edits);

  recordTool(trace, {
    name: formatObservationName("edit-file", input.file_path?.split("/").pop()),
    input: { file_path: input.file_path, extension },
    output: {
      edit_count: editStats.editCount,
      edits: input.edits?.map((e) => ({
        range: e.range,
        old_line: e.old_line,
        new_line: e.new_line,
      })),
    },
    metadata: { file_extension: extension, source: "tab", ...editStats },
  });

  return null;
}

export function routeHookHandler(hookName, trace, input) {
  const handlers = {
    sessionStart: handleSessionStart,
    sessionEnd: handleSessionEnd,
    beforeSubmitPrompt: handleBeforeSubmitPrompt,
    afterAgentResponse: handleAfterAgentResponse,
    afterAgentThought: handleAfterAgentThought,
    preToolUse: handlePreToolUse,
    beforeShellExecution: handleBeforeShellExecution,
    afterShellExecution: handleAfterShellExecution,
    beforeMCPExecution: handleBeforeMCPExecution,
    afterMCPExecution: handleAfterMCPExecution,
    beforeReadFile: handleBeforeReadFile,
    afterFileEdit: handleAfterFileEdit,
    postToolUse: handlePostToolUse,
    postToolUseFailure: handlePostToolUseFailure,
    subagentStart: handleSubagentStart,
    subagentStop: handleSubagentStop,
    stop: handleStop,
    beforeTabFileRead: handleBeforeTabFileRead,
    afterTabFileEdit: handleAfterTabFileEdit,
  };

  const handler = handlers[hookName];
  if (!handler) {
    console.error(`Unknown hook type: ${hookName}`);
    return { continue: true, permission: "allow" };
  }

  return handler(trace, input);
}
