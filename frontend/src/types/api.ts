export type BoardType = "fixed" | "randomized";
export type LockoutMode = "non_lockout" | "lockout";

export interface RoomDTO {
  id: string;
  name: string;
  hide_card: boolean;
  created_at: string;
}

export interface GameDTO {
  id: number;
  rows: number;
  cols: number;
  board_type: BoardType;
  lockout_mode: LockoutMode;
  seed: string;
  created_at: string;
}

export interface PlayerDTO {
  id: string;
  name: string;
  color: string;
  is_spectator: boolean;
  connected: boolean;
}

export interface SquareDTO {
  row: number;
  col: number;
  goal: string;
  colors: string[];
}

export interface GoalEventPayload {
  row: number;
  col: number;
  goal: string;
  colors: string[];
  color: string;
  remove: boolean;
}

export interface ColorEventPayload {
  color: string;
}

export interface ChatEventPayload {
  text: string;
}

export interface ConnectionEventPayload {
  connected: boolean;
}

export interface NewCardEventPayload {
  game_id: number;
  seed: string;
  hide_card: boolean;
}

interface EventBase {
  player: PlayerDTO;
  /** The player's colour when the event happened, not their colour now -
   * the backend snapshots it so old feed entries keep their original colour. */
  player_color: string;
  created_at: string;
}

/** Discriminated on `type`, so `event.payload` narrows automatically and
 * switches over event kinds are checked for exhaustiveness. Mirrors
 * Event.Type in backend/rooms/models.py. */
export type EventDTO =
  | (EventBase & { type: "goal"; payload: GoalEventPayload })
  | (EventBase & { type: "color"; payload: ColorEventPayload })
  | (EventBase & { type: "chat"; payload: ChatEventPayload })
  | (EventBase & { type: "connection"; payload: ConnectionEventPayload })
  | (EventBase & { type: "revealed"; payload: Record<string, never> })
  | (EventBase & { type: "new_card"; payload: NewCardEventPayload });

export type EventType = EventDTO["type"];

export interface RoomSessionDTO {
  room: RoomDTO;
  player: PlayerDTO;
  token: string;
}

export interface RoomSettingsDTO {
  room: RoomDTO;
  game: GameDTO;
}
