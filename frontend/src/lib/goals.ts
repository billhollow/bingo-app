/** One goal per line, blanks dropped - the format both goal textareas use. */
export function parseGoals(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}
