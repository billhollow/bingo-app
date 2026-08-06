import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as roomsApi from "../lib/rooms-api";
import type {
  ColorEventPayload,
  ConnectionEventPayload,
  EventDTO,
  GameDTO,
  GoalEventPayload,
  PlayerDTO,
  RoomDTO,
  SquareDTO,
} from "../types/api";

export const useRoomStore = defineStore("room", () => {
  const roomId = ref<string | null>(null);
  const token = ref<string | null>(null);
  const currentPlayerId = ref<string | null>(null);

  const room = ref<RoomDTO | null>(null);
  const game = ref<GameDTO | null>(null);
  const squares = ref<SquareDTO[]>([]);
  const players = ref<PlayerDTO[]>([]);
  const events = ref<EventDTO[]>([]);
  const cardRevealed = ref(false);

  const currentPlayer = computed(() => players.value.find((p) => p.id === currentPlayerId.value) ?? null);

  function requireCreds(): { id: string; authToken: string } {
    if (!roomId.value || !token.value) {
      throw new Error("Room store used before load()");
    }
    return { id: roomId.value, authToken: token.value };
  }

  async function load(id: string, authToken: string, playerId: string) {
    roomId.value = id;
    token.value = authToken;
    currentPlayerId.value = playerId;
    cardRevealed.value = false;

    const [settings, boardData, playersData, feed] = await Promise.all([
      roomsApi.fetchSettings(id, authToken),
      roomsApi.fetchBoard(id, authToken),
      roomsApi.fetchPlayers(id, authToken),
      roomsApi.fetchFeed(id, authToken),
    ]);

    room.value = settings.room;
    game.value = settings.game;
    squares.value = boardData;
    players.value = playersData;
    events.value = feed;
  }

  async function refreshBoardAndSettings() {
    const { id, authToken } = requireCreds();
    const [settings, boardData] = await Promise.all([
      roomsApi.fetchSettings(id, authToken),
      roomsApi.fetchBoard(id, authToken),
    ]);
    room.value = settings.room;
    game.value = settings.game;
    squares.value = boardData;
    cardRevealed.value = false;
  }

  function applyEvent(event: EventDTO) {
    events.value.push(event);

    switch (event.type) {
      case "goal": {
        const payload = event.payload as GoalEventPayload;
        const square = squares.value.find((s) => s.row === payload.row && s.col === payload.col);
        if (square) square.colors = payload.colors;
        break;
      }
      case "color": {
        const player = players.value.find((p) => p.id === event.player.id);
        if (player) player.color = (event.payload as ColorEventPayload).color;
        break;
      }
      case "connection": {
        const connected = (event.payload as ConnectionEventPayload).connected;
        const existing = players.value.find((p) => p.id === event.player.id);
        if (existing) {
          existing.connected = connected;
        } else if (connected) {
          players.value.push(event.player);
        }
        break;
      }
      case "revealed": {
        if (event.player.id === currentPlayerId.value) cardRevealed.value = true;
        break;
      }
      case "new_card": {
        void refreshBoardAndSettings();
        break;
      }
      case "chat":
        break;
    }
  }

  async function toggleSquare(row: number, col: number, color: string, remove: boolean) {
    const { id, authToken } = requireCreds();
    await roomsApi.markSquare(id, authToken, { row, col, color, remove });
  }

  async function setColor(color: string) {
    const { id, authToken } = requireCreds();
    await roomsApi.changeColor(id, authToken, color);
  }

  async function postChat(text: string) {
    const { id, authToken } = requireCreds();
    await roomsApi.sendChat(id, authToken, text);
  }

  async function reveal() {
    const { id, authToken } = requireCreds();
    await roomsApi.revealCard(id, authToken);
    cardRevealed.value = true;
  }

  async function newCard(input: roomsApi.NewCardInput) {
    const { id, authToken } = requireCreds();
    await roomsApi.startNewCard(id, authToken, input);
  }

  function cellColors(row: number, col: number): string[] {
    return squares.value.find((s) => s.row === row && s.col === col)?.colors ?? [];
  }

  function squareCountForColor(color: string): number {
    return squares.value.filter((s) => s.colors.includes(color)).length;
  }

  function lineCountForColor(color: string): number {
    if (!game.value) return 0;
    const { rows, cols } = game.value;
    let count = 0;

    for (let row = 0; row < rows; row++) {
      if (allMatch(cols, (col) => cellColors(row, col).includes(color))) count++;
    }
    for (let col = 0; col < cols; col++) {
      if (allMatch(rows, (row) => cellColors(row, col).includes(color))) count++;
    }
    if (rows === cols) {
      if (allMatch(rows, (i) => cellColors(i, i).includes(color))) count++;
      if (allMatch(rows, (i) => cellColors(i, rows - 1 - i).includes(color))) count++;
    }
    return count;
  }

  return {
    roomId,
    token,
    currentPlayerId,
    currentPlayer,
    room,
    game,
    squares,
    players,
    events,
    cardRevealed,
    load,
    applyEvent,
    toggleSquare,
    setColor,
    postChat,
    reveal,
    newCard,
    cellColors,
    squareCountForColor,
    lineCountForColor,
  };
});

function allMatch(length: number, predicate: (index: number) => boolean): boolean {
  for (let i = 0; i < length; i++) {
    if (!predicate(i)) return false;
  }
  return true;
}
