/**
 * Utility functions for Cursor Langfuse hooks
 */

/**
 * Read and parse JSON input from stdin
 * Cursor hooks pass data via stdin as JSON
 * @returns {Promise<object>} Parsed JSON object from stdin
 */
export async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => {
      try {
        // Cursor on Windows may prefix stdin with a UTF-8 BOM (\uFEFF).
        const cleaned = data.replace(/^\uFEFF/, '').trim();
        resolve(JSON.parse(cleaned));
      } catch (e) {
        reject(new Error(`Failed to parse JSON from stdin: ${e.message}`));
      }
    });
    process.stdin.on('error', reject);
  });
}

/**
 * Generate a descriptive trace name from the prompt
 * @param {string} prompt - The user's prompt text
 * @param {string} model - The model being used
 * @returns {string} A descriptive trace name
 */
export function generateTraceName(prompt, model) {
  if (!prompt) {
    return `Cursor ${model || 'Agent'}`;
  }
  
  // Extract first meaningful words from the prompt (max 50 chars)
  const cleaned = prompt
    .replace(/\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  
  const maxLength = 50;
  if (cleaned.length <= maxLength) {
    return cleaned;
  }
  
  // Try to cut at a word boundary
  const truncated = cleaned.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > 30) {
    return truncated.substring(0, lastSpace) + '...';
  }
  
  return truncated + '...';
}

/**
 * Session ID from conversation_id — one Langfuse session per Cursor chat.
 * Includes environment so Sessions filtered by production/development stay correct
 * (Langfuse pins session.environment from the first trace that creates it).
 * @param {string} conversationId
 * @param {string} [environment]
 * @returns {string}
 */
export function generateSessionId(conversationId, environment = "development") {
  const env = String(environment || "development")
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "")
    .slice(0, 32) || "development";

  if (!conversationId) {
    return `cursor-${env}-unknown`;
  }

  // US-ASCII, max 200 chars (Langfuse drops longer sessionIds).
  return `cursor-${env}-${conversationId}`.slice(0, 200);
}

/**
 * Cursor sometimes suffixes generation_id for thinking hooks
 * (e.g. "<uuid>-0-abcd"). Collapse those onto the parent turn trace.
 * @param {string|null|undefined} generationId
 * @returns {string|null}
 */
export function normalizeGenerationId(generationId) {
  if (!generationId) return null;
  const raw = String(generationId);
  const match = raw.match(
    /^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:-.*)?$/i
  );
  return match ? match[1] : raw;
}

/**
 * Tags set once at trace creation (immutable in Langfuse).
 * Business-level dimensions only — not per-tool activity.
 * @param {object} input - Hook input with model, workspace_roots, hook_event_name
 * @returns {string[]}
 */
export function generateTraceTags(input) {
  const tags = ["cursor"];

  if (input.hook_event_name?.includes("Tab")) {
    tags.push("tab");
  } else {
    tags.push("agent");
  }

  if (input.workspace_roots?.length > 0) {
    const folder = input.workspace_roots[0].split("/").pop();
    if (folder) {
      tags.push(`workspace-${folder.toLowerCase().replace(/[^a-z0-9-]/g, "-").substring(0, 30)}`);
    }
  }

  return tags;
}

/**
 * Determine the observation level based on status or context
 * @param {string} status - The status (e.g., 'completed', 'error', 'aborted')
 * @param {boolean} isBlocked - Whether the operation was blocked
 * @returns {string} Level: 'DEBUG' | 'DEFAULT' | 'WARNING' | 'ERROR'
 */
export function determineLevel(status, isBlocked = false) {
  if (isBlocked) {
    return 'WARNING';
  }
  
  switch (status) {
    case 'error':
      return 'ERROR';
    case 'aborted':
      return 'WARNING';
    case 'completed':
    default:
      return 'DEFAULT';
  }
}

/**
 * Calculate edit statistics from an array of edits
 * @param {Array<{old_string: string, new_string: string}>} edits - Array of edits
 * @returns {object} Edit statistics
 */
export function calculateEditStats(edits) {
  if (!edits || !Array.isArray(edits)) {
    return { editCount: 0, linesAdded: 0, linesRemoved: 0 };
  }
  
  let linesAdded = 0;
  let linesRemoved = 0;
  
  for (const edit of edits) {
    const oldLines = (edit.old_string || '').split('\n').length;
    const newLines = (edit.new_string || '').split('\n').length;
    
    if (newLines > oldLines) {
      linesAdded += newLines - oldLines;
    } else if (oldLines > newLines) {
      linesRemoved += oldLines - newLines;
    }
  }
  
  return {
    editCount: edits.length,
    linesAdded,
    linesRemoved,
    netChange: linesAdded - linesRemoved,
  };
}

/**
 * Extract file extension from a file path
 * @param {string} filePath - The file path
 * @returns {string} The file extension (without dot) or 'unknown'
 */
export function getFileExtension(filePath) {
  if (!filePath) return 'unknown';
  
  const parts = filePath.split('.');
  if (parts.length < 2) return 'unknown';
  
  return parts.pop().toLowerCase();
}

/**
 * Parse tool_output from postToolUse hooks (JSON string or raw value)
 * @param {unknown} toolOutput
 * @returns {unknown}
 */
export function parseToolOutput(toolOutput) {
  if (toolOutput == null || toolOutput === '') {
    return null;
  }

  if (typeof toolOutput !== 'string') {
    return toolOutput;
  }

  try {
    return JSON.parse(toolOutput);
  } catch {
    return toolOutput;
  }
}

export function formatDuration(ms) {
  if (!ms || ms < 0) return '0ms';
  
  if (ms < 1000) {
    return `${ms}ms`;
  }
  
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  
  const minutes = Math.floor(ms / 60000);
  const seconds = ((ms % 60000) / 1000).toFixed(0);
  return `${minutes}m ${seconds}s`;
}

