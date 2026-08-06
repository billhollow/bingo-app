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

export type EventType = "chat" | "goal" | "color" | "revealed" | "connection" | "new_card";

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

export type EventPayload =
  | GoalEventPayload
  | ColorEventPayload
  | ChatEventPayload
  | ConnectionEventPayload
  | NewCardEventPayload
  | Record<string, never>;

export interface EventDTO {
  type: EventType;
  player: PlayerDTO;
  player_color: string;
  payload: EventPayload;
  created_at: string;
}

export interface RoomSessionDTO {
  room: RoomDTO;
  player: PlayerDTO;
  token: string;
}

export interface RoomSettingsDTO {
  room: RoomDTO;
  game: GameDTO;
}
