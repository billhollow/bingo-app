/** Either the goals a textarea yielded, or why its contents couldn't be read. */
export type GoalParseResult = { ok: true; goals: string[] } | { ok: false; error: string };

/** Goals as one-per-line text, or as a pasted JSON array.
 *
 * Published goal lists (bingosync's included) ship as JSON - either bare strings or
 * objects carrying a `name` alongside metadata we don't use - so accepting a paste
 * directly saves stripping it by hand. Line splitting a pretty-printed array counts
 * every brace as a goal, so once the text looks like JSON we never fall back to it. */
export function parseGoals(text: string): GoalParseResult {
  const trimmed = text.trim();
  if (trimmed.startsWith("[") || trimmed.startsWith("{")) return parseJsonGoals(trimmed);

  return { ok: true, goals: splitLines(text) };
}

function splitLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function parseJsonGoals(text: string): GoalParseResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `That looks like JSON but couldn't be parsed: ${detail}` };
  }

  if (!Array.isArray(parsed)) {
    return { ok: false, error: "That JSON is not a list of goals." };
  }

  const goals: string[] = [];
  for (const [index, item] of parsed.entries()) {
    const name = goalName(item);
    if (name === null) {
      return {
        ok: false,
        error: `Item ${index + 1} is not a goal (expected a string or an object with a "name").`,
      };
    }
    if (name.length > 0) goals.push(name);
  }

  return { ok: true, goals };
}

function goalName(item: unknown): string | null {
  if (typeof item === "string") return item.trim();
  if (item !== null && typeof item === "object" && "name" in item) {
    const name = (item as { name: unknown }).name;
    if (typeof name === "string") return name.trim();
  }
  return null;
}
