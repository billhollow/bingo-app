import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { roomClient, type NewCardInput, type RoomClient } from "../lib/rooms-api";
import type { EventDTO, GameDTO, PlayerDTO, RoomDTO, SquareDTO } from "../types/api";

export const useRoomStore = defineStore("room", () => {
  const currentPlayerId = ref<string | null>(null);

  const room = ref<RoomDTO | null>(null);
  const game = ref<GameDTO | null>(null);
  const squares = ref<SquareDTO[]>([]);
  const players = ref<PlayerDTO[]>([]);
  const events = ref<EventDTO[]>([]);
  const cardRevealed = ref(false);

  const currentPlayer = computed(() => players.value.find((p) => p.id === currentPlayerId.value) ?? null);

  // Bound to the room + token by load(); every action goes through it, so the
  // room id and token are never threaded through call sites.
  let boundClient: RoomClient | null = null;

  function api(): RoomClient {
    if (!boundClient) throw new Error("Room store used before load()");
    return boundClient;
  }

  async function load(id: string, authToken: string, playerId: string) {
    boundClient = roomClient(id, authToken);
    currentPlayerId.value = playerId;
    cardRevealed.value = false;

    const [settings, boardData, playersData, feed] = await Promise.all([
      api().settings(),
      api().board(),
      api().players(),
      api().feed(),
    ]);

    room.value = settings.room;
    game.value = settings.game;
    squares.value = boardData;
    players.value = playersData;
    events.value = feed;
  }

  async function refreshBoardAndSettings() {
    const [settings, boardData] = await Promise.all([api().settings(), api().board()]);
    room.value = settings.room;
    game.value = settings.game;
    squares.value = boardData;
    cardRevealed.value = false;
  }

  function applyEvent(event: EventDTO) {
    events.value.push(event);

    switch (event.type) {
      case "goal": {
        const square = squareAt(event.payload.row, event.payload.col);
        if (square) square.colors = event.payload.colors;
        break;
      }
      case "color": {
        const player = players.value.find((p) => p.id === event.player.id);
        if (player) player.color = event.payload.color;
        break;
      }
      case "connection": {
        const { connected } = event.payload;
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
    await api().markSquare({ row, col, color, remove });
  }

  async function setColor(color: string) {
    await api().changeColor(color);
  }

  async function postChat(text: string) {
    await api().chat(text);
  }

  async function reveal() {
    await api().reveal();
    cardRevealed.value = true;
  }

  async function newCard(input: NewCardInput) {
    await api().newCard(input);
  }

  function squareAt(row: number, col: number): SquareDTO | undefined {
    return squares.value.find((s) => s.row === row && s.col === col);
  }

  function cellColors(row: number, col: number): string[] {
    return squareAt(row, col)?.colors ?? [];
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
