// Mirrors backend/rooms/colors.py's Color enum (minus BLANK).
export const PLAYER_COLORS = [
  "red",
  "blue",
  "green",
  "orange",
  "purple",
  "navy",
  "teal",
  "pink",
  "brown",
  "yellow",
] as const;

export type PlayerColor = (typeof PLAYER_COLORS)[number];

export const COLOR_HEX: Record<PlayerColor, string> = {
  red: "#e53e3e",
  blue: "#3182ce",
  green: "#38a169",
  orange: "#dd6b20",
  purple: "#805ad5",
  navy: "#2c3e70",
  teal: "#319795",
  pink: "#d53f8c",
  brown: "#8b5e3c",
  yellow: "#d69e2e",
};

function hexFor(color: string): string {
  return COLOR_HEX[color as PlayerColor] ?? "#999999";
}

/** CSS `background` value for a square: solid for one color, evenly-striped
 * diagonal bands for several overlapping marks (non-lockout mode), nothing
 * for a blank square. */
export function squareBackground(colors: string[]): string {
  if (colors.length === 0) return "transparent";
  if (colors.length === 1) return hexFor(colors[0]);

  const step = 100 / colors.length;
  const stops = colors.flatMap((color, index) => {
    const hex = hexFor(color);
    return [`${hex} ${index * step}%`, `${hex} ${(index + 1) * step}%`];
  });
  return `linear-gradient(135deg, ${stops.join(", ")})`;
}
