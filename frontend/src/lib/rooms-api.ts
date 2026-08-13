import { apiGet, apiPost } from "./api";
import type {
  BoardType,
  EventDTO,
  GameDTO,
  LockoutMode,
  PlayerDTO,
  RoomSessionDTO,
  RoomSettingsDTO,
  SquareDTO,
} from "../types/api";

export interface CreateRoomInput {
  name: string;
  passphrase: string;
  creator_name: string;
  goals: string[];
  board_type?: BoardType;
  rows?: number;
  cols?: number;
  lockout_mode?: LockoutMode;
  seed?: string;
  hide_card?: boolean;
  is_spectator?: boolean;
}

export interface JoinRoomInput {
  passphrase: string;
  player_name: string;
  is_spectator?: boolean;
}

export interface NewCardInput {
  goals: string[];
  board_type?: BoardType;
  rows?: number;
  cols?: number;
  lockout_mode?: LockoutMode;
  seed?: string;
  hide_card?: boolean;
}

export interface MarkSquareInput {
  row: number;
  col: number;
  color: string;
  remove?: boolean;
}

// The two endpoints you can reach without a token, because they're how you
// get one.

export function createRoom(input: CreateRoomInput) {
  return apiPost<RoomSessionDTO>("/api/rooms/", input);
}

export function joinRoom(roomId: string, input: JoinRoomInput) {
  return apiPost<RoomSessionDTO>(`/api/rooms/${roomId}/join/`, input);
}

/** Every room-scoped endpoint, bound to one room and token.
 *
 * Mirrors the nesting in backend/rooms/urls.py: the `/api/rooms/<id>/` prefix
 * and the bearer token are each written once here, so callers name only the
 * action. The room store builds one of these in load() and holds it. */
export function roomClient(roomId: string, token: string) {
  const path = (suffix: string) => `/api/rooms/${roomId}/${suffix}`;
  const auth = { token };

  return {
    board: () => apiGet<SquareDTO[]>(path("board/"), auth),
    settings: () => apiGet<RoomSettingsDTO>(path("settings/"), auth),
    players: () => apiGet<PlayerDTO[]>(path("players/"), auth),
    feed: () => apiGet<EventDTO[]>(path("feed/"), auth),
    newCard: (input: NewCardInput) => apiPost<GameDTO>(path("new-card/"), input, auth),
    markSquare: (input: MarkSquareInput) => apiPost<EventDTO>(path("goal/"), input, auth),
    changeColor: (color: string) => apiPost<EventDTO>(path("color/"), { color }, auth),
    chat: (text: string) => apiPost<EventDTO>(path("chat/"), { text }, auth),
    reveal: () => apiPost<EventDTO>(path("reveal/"), {}, auth),
  };
}

export type RoomClient = ReturnType<typeof roomClient>;
