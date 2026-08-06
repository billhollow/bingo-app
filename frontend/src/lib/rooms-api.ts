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

export function createRoom(input: CreateRoomInput) {
  return apiPost<RoomSessionDTO>("/api/rooms/", input);
}

export interface JoinRoomInput {
  passphrase: string;
  player_name: string;
  is_spectator?: boolean;
}

export function joinRoom(roomId: string, input: JoinRoomInput) {
  return apiPost<RoomSessionDTO>(`/api/rooms/${roomId}/join/`, input);
}

export function fetchBoard(roomId: string, token: string) {
  return apiGet<SquareDTO[]>(`/api/rooms/${roomId}/board/`, { token });
}

export function fetchSettings(roomId: string, token: string) {
  return apiGet<RoomSettingsDTO>(`/api/rooms/${roomId}/settings/`, { token });
}

export function fetchPlayers(roomId: string, token: string) {
  return apiGet<PlayerDTO[]>(`/api/rooms/${roomId}/players/`, { token });
}

export function fetchFeed(roomId: string, token: string) {
  return apiGet<EventDTO[]>(`/api/rooms/${roomId}/feed/`, { token });
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

export function startNewCard(roomId: string, token: string, input: NewCardInput) {
  return apiPost<GameDTO>(`/api/rooms/${roomId}/new-card/`, input, { token });
}

export interface MarkSquareInput {
  row: number;
  col: number;
  color: string;
  remove?: boolean;
}

export function markSquare(roomId: string, token: string, input: MarkSquareInput) {
  return apiPost<EventDTO>(`/api/rooms/${roomId}/goal/`, input, { token });
}

export function changeColor(roomId: string, token: string, color: string) {
  return apiPost<EventDTO>(`/api/rooms/${roomId}/color/`, { color }, { token });
}

export function sendChat(roomId: string, token: string, text: string) {
  return apiPost<EventDTO>(`/api/rooms/${roomId}/chat/`, { text }, { token });
}

export function revealCard(roomId: string, token: string) {
  return apiPost<EventDTO>(`/api/rooms/${roomId}/reveal/`, {}, { token });
}
