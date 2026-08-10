/**
 * Keep Langfuse payloads small so flush finishes inside Cursor hook timeouts.
 */

export const MAX_STRING_CHARS = 24_000;
export const MAX_JSON_CHARS = 48_000;

export function truncateString(value, max = MAX_STRING_CHARS) {
  if (value == null) return value;
  const text = typeof value === "string" ? value : String(value);
  if (text.length <= max) return text;
  return `${text.slice(0, max)}\n…[truncated ${text.length - max} chars]`;
}

export function truncateJson(value, max = MAX_JSON_CHARS) {
  if (value == null) return value;
  if (typeof value === "string") return truncateString(value, max);

  try {
    const serialized = JSON.stringify(value);
    if (serialized.length <= max) return value;
    return {
      truncated: true,
      preview: serialized.slice(0, Math.min(max, 8_000)),
      original_length: serialized.length,
    };
  } catch {
    return { truncated: true, reason: "unserializable" };
  }
}
