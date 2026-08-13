import type { BoardType, LockoutMode } from "../types/api";

/** The board options shared by "create room" and "new card". Both forms own a
 * reactive object of this shape and hand it to <BoardConfigFields>. */
export interface BoardConfig {
  boardType: BoardType;
  rows: number;
  cols: number;
  lockoutMode: LockoutMode;
  hideCard: boolean;
}

/** User-facing names for LockoutMode, so the picker and the "current mode"
 * readout in the settings panel can't drift apart. */
export const LOCKOUT_MODE_LABELS: Record<LockoutMode, string> = {
  non_lockout: "Non-Lockout",
  lockout: "Lockout",
};
