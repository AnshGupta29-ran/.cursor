/**
 * Re-run ripgrep to capture Grep tool results for Langfuse.
 *
 * Cursor's postToolUse tool_output for Grep often only includes metadata
 * (e.g. { pattern, success }) without the actual matches/files.
 */

import { spawnSync } from "child_process";

const RESULT_KEYS = [
  "files",
  "matches",
  "results",
  "content",
  "stdout",
  "paths",
  "data",
  "output",
  "text",
];

function hasSubstantiveGrepOutput(parsedOutput) {
  if (parsedOutput == null) return false;
  if (typeof parsedOutput === "string") return parsedOutput.length > 0;

  if (typeof parsedOutput !== "object") return false;

  for (const key of RESULT_KEYS) {
    const value = parsedOutput[key];
    if (value == null) continue;
    if (typeof value === "string" && value.length > 0) return true;
    if (Array.isArray(value) && value.length > 0) return true;
    if (typeof value === "object" && Object.keys(value).length > 0) return true;
  }

  return false;
}

function resolveRgBinary() {
  const cursorRg =
    "/Applications/Cursor.app/Contents/Resources/app/node_modules/@vscode/ripgrep/bin/rg";
  const candidates = [process.env.RG_PATH, "rg", cursorRg].filter(Boolean);

  for (const candidate of candidates) {
    const check = spawnSync(candidate, ["--version"], { encoding: "utf8" });
    if (check.status === 0) return candidate;
  }

  return "rg";
}

/**
 * Build and run an rg command equivalent to Cursor's Grep tool input.
 * @param {object} toolInput
 * @returns {object}
 */
export function captureGrepResults(toolInput) {
  const pattern =
    toolInput.pattern ?? toolInput.regex ?? toolInput.query ?? toolInput.q ?? "";
  const searchPath = toolInput.path ?? toolInput.file_path ?? process.cwd();
  const glob = toolInput.glob;
  const outputMode = toolInput.output_mode ?? "content";
  const rg = resolveRgBinary();
  const args = ["--no-heading", "--color=never"];

  if (toolInput["-i"] || toolInput.case_insensitive) args.push("-i");
  if (toolInput.multiline) args.push("-U", "--multiline-dotall");
  if (toolInput["-A"] != null) args.push("-A", String(toolInput["-A"]));
  if (toolInput["-B"] != null) args.push("-B", String(toolInput["-B"]));
  if (toolInput["-C"] != null) args.push("-C", String(toolInput["-C"]));
  if (toolInput.type) args.push("--type", toolInput.type);
  if (glob) args.push("--glob", glob);

  if (outputMode === "files_with_matches") {
    args.push("-l");
  } else if (outputMode === "count") {
    args.push("-c");
  }

  if (!pattern) {
    if (outputMode === "files_with_matches") {
      args.length = 0;
      args.push("--files", "--color=never");
      if (glob) args.push("--glob", glob);
      args.push(searchPath);
    } else {
      return {
        pattern,
        output_mode: outputMode,
        files: [],
        matches: "",
        note: "empty pattern — no content/count results to capture",
      };
    }
  } else {
    args.push(pattern, searchPath);
  }

  if (toolInput.head_limit != null && Number.isFinite(toolInput.head_limit)) {
    args.push("--max-count", String(toolInput.head_limit));
  }

  const result = spawnSync(rg, args, {
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });

  const stdout = (result.stdout || "").trim();
  const stderr = (result.stderr || "").trim();
  const lines = stdout ? stdout.split("\n").filter(Boolean) : [];

  const output = {
    pattern,
    output_mode: outputMode,
    search_path: searchPath,
    exit_code: result.status,
    stdout,
  };

  if (stderr) output.stderr = stderr;

  if (outputMode === "files_with_matches") {
    output.files = lines;
    output.file_count = lines.length;
  } else if (outputMode === "count") {
    output.counts = lines;
    output.match_count = lines.length;
  } else {
    output.matches = stdout;
    output.match_line_count = lines.length;
  }

  return output;
}

/**
 * Return substantive Grep output, re-running rg when Cursor omits results.
 * @param {unknown} parsedOutput
 * @param {object} toolInput
 * @returns {object}
 */
export function enrichGrepOutput(parsedOutput, toolInput) {
  if (hasSubstantiveGrepOutput(parsedOutput)) {
    return parsedOutput;
  }

  try {
    const captured = captureGrepResults(toolInput);
    return {
      cursor_tool_output: parsedOutput,
      ...captured,
    };
  } catch (error) {
    return {
      cursor_tool_output: parsedOutput,
      enrichment_error: error.message,
    };
  }
}

export function grepSpanLabel(toolInput) {
  const pattern =
    toolInput.pattern ?? toolInput.regex ?? toolInput.query ?? toolInput.q;
  if (pattern) return pattern.substring(0, 60);
  if (toolInput.glob) return `glob:${toolInput.glob}`.substring(0, 60);
  const path = toolInput.path ?? toolInput.file_path;
  if (path) return path.split("/").pop() || "search";
  return "search";
}
