/**
 * Langfuse observation helpers aligned with:
 * https://langfuse.com/faq/all/what-does-a-good-trace-look-like
 *
 * - Trace  = one agent turn (user prompt → response)
 * - Session = multi-turn conversation
 * - Tools  = one observation per tool call, named by action
 * - Generations = LLM outputs only
 */

import { readFileSync } from "fs";
import { formatDuration, getFileExtension } from "./utils.js";
import { truncateJson, truncateString } from "./payload.js";

/**
 * Semantic tool names (action-based, not model-based).
 */
export function toolName(toolName, toolInput = {}) {
  switch (toolName) {
    case "Grep":
      return "grep-search";
    case "Read":
      return "read-file";
    case "Write":
    case "StrReplace":
      return "edit-file";
    case "Delete":
      return "delete-file";
    case "Shell":
      return "shell-exec";
    case "Task":
      return "task-spawn";
    case "Glob":
      return "glob-search";
    case "EditNotebook":
      return "edit-notebook";
    default:
      if (toolName?.startsWith("MCP:")) {
        const mcpTool = toolName.replace(/^MCP:\s*/, "");
        return `mcp-${mcpTool.toLowerCase().replace(/[^a-z0-9-]/g, "-").substring(0, 40)}`;
      }
      return (
        toolName?.toLowerCase().replace(/[^a-z0-9-]/g, "-").substring(0, 40) ||
        "tool-call"
      );
  }
}

export function toolDescription(toolName, toolInput = {}) {
  switch (toolName) {
    case "Grep": {
      const pattern =
        toolInput.pattern ?? toolInput.regex ?? toolInput.query ?? toolInput.q;
      return pattern ? pattern.substring(0, 80) : "search";
    }
    case "Read":
    case "Write":
    case "StrReplace":
    case "Delete": {
      const path = toolInput.path ?? toolInput.file_path ?? toolInput.target_notebook;
      return path?.split("/").pop() || "file";
    }
    case "Shell":
      return (toolInput.command ?? "command").substring(0, 80);
    case "Glob":
      return (toolInput.glob_pattern ?? "pattern").substring(0, 80);
    case "Task":
      return (toolInput.description ?? toolInput.subagent_type ?? "subagent").substring(
        0,
        80
      );
    default:
      if (toolName?.startsWith("MCP:")) {
        return toolInput.toolName ?? toolName.replace(/^MCP:\s*/, "");
      }
      return toolName ?? "tool";
  }
}

function metadataToolName(observationName) {
  if (!observationName) return "tool-call";
  const separatorIndex = observationName.indexOf(": ");
  return separatorIndex === -1
    ? observationName
    : observationName.substring(0, separatorIndex);
}

/**
 * Record a completed tool call as a single observation.
 * Uses span under the hood (SDK v3); metadata marks intent for tool filtering.
 */
export function recordTool(trace, { name, input, output, metadata = {}, durationMs, level }) {
  if (!trace) return;
  trace
    .span({
      name,
      input: truncateJson(input),
      output: truncateJson(output),
      level: level ?? "DEFAULT",
      metadata: {
        observation_type: "tool",
        tool_name: metadata.tool_name ?? metadataToolName(name),
        ...metadata,
        ...(durationMs != null && {
          duration_ms: durationMs,
          duration_formatted: formatDuration(durationMs),
        }),
      },
    })
    .end();
}

/**
 * Record an LLM generation (agent response, not the user prompt).
 */
export function recordGeneration(trace, { name, input, output, model, metadata = {} }) {
  if (!trace) return;
  trace.generation({
    name,
    input: truncateJson(input),
    output: truncateString(output),
    model,
    metadata,
  });
}

export function buildReadToolInput(filePath, content) {
  return {
    file_path: filePath,
    extension: getFileExtension(filePath),
    ...(content != null && { content_length: content.length }),
  };
}

export function buildReadToolOutput(content) {
  if (content == null) return null;
  return content.length > 50_000
    ? { truncated: true, preview: content.substring(0, 50_000), total_length: content.length }
    : content;
}

export function buildShellToolInput(command, cwd) {
  return { command, ...(cwd && { cwd }) };
}

function offsetToRange(content, startOffset, endOffset) {
  let line = 1;
  let column = 1;
  let start = null;
  let end = null;

  for (let i = 0; i <= content.length; i++) {
    if (i === startOffset) {
      start = {
        start_line_number: line,
        start_column: column,
      };
    }

    if (i === endOffset) {
      end = {
        end_line_number: line,
        end_column: column,
      };
      break;
    }

    if (content[i] === "\n") {
      line++;
      column = 1;
    } else {
      column++;
    }
  }

  return start && end ? { ...start, ...end } : null;
}

function inferEditLocations(filePath, edits) {
  if (!filePath || !Array.isArray(edits) || edits.length === 0) {
    return edits;
  }

  let content;
  try {
    content = readFileSync(filePath, "utf8");
  } catch {
    return edits.map((edit) => ({
      ...edit,
      location_status: "unavailable",
      location_reason: "unable to read final file contents",
    }));
  }

  let searchOffset = 0;

  return edits.map((edit) => {
    const textToLocate = edit.new_string || "";
    if (!textToLocate) {
      return {
        ...edit,
        location_status: "unavailable",
        location_reason: "deletions cannot be located from afterFileEdit final-file payload",
      };
    }

    let startOffset = content.indexOf(textToLocate, searchOffset);
    let location_source = "matched_new_string_forward";

    if (startOffset === -1) {
      startOffset = content.indexOf(textToLocate);
      location_source = "matched_new_string_global";
    }

    if (startOffset === -1) {
      return {
        ...edit,
        location_status: "unavailable",
        location_reason: "could not match new_string in final file contents",
      };
    }

    const endOffset = startOffset + textToLocate.length;
    const range = offsetToRange(content, startOffset, endOffset);
    searchOffset = endOffset;

    return {
      ...edit,
      ...(range && { range }),
      location_status: range ? "inferred" : "unavailable",
      ...(range
        ? { location_source }
        : { location_reason: "matched text but could not convert offset to range" }),
    };
  });
}

export function buildEditToolOutput(filePath, edits, editStats) {
  return {
    edit_count: editStats.editCount,
    lines_added: editStats.linesAdded,
    lines_removed: editStats.linesRemoved,
    net_change: editStats.netChange,
    edits: inferEditLocations(filePath, edits),
  };
}

/**
 * Record agent/subagent thinking as a generation (LLM reasoning) or span fallback.
 * Uses a stable id when provided to dedupe across fallback sources.
 */
export function recordThinking(trace, { text, model, durationMs, source, metadata = {}, id }) {
  if (!trace || !text?.trim()) return false;

  const name = source === "subagent" ? "subagent-thinking" : "agent-thinking";
  const body = {
    ...(id && { id }),
    name,
    output: truncateString(text),
    metadata: {
      observation_type: "thinking",
      source,
      thinking_length: text.length,
      ...(durationMs != null && {
        duration_ms: durationMs,
        duration_formatted: formatDuration(durationMs),
      }),
      ...metadata,
    },
  };

  if (model) {
    trace.generation({
      ...body,
      model,
      input: { type: "thinking" },
    });
  } else {
    trace.span(body).end();
  }

  return true;
}

/**
 * Flush queued pre-tool reasoning when afterAgentThought never fired for this turn.
 */
export function flushPendingThinking(trace, generationId, consumePending, hasCaptured, cleanup) {
  if (hasCaptured(generationId)) {
    cleanup(generationId);
    return 0;
  }

  const pending = consumePending(generationId);
  let count = 0;

  for (const entry of pending) {
    if (recordThinking(trace, entry)) count++;
  }

  cleanup(generationId);
  return count;
}
