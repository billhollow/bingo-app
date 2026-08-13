<script setup lang="ts">
import { computed } from "vue";

import { squareBackground } from "../../lib/colors";
import { useRoomStore } from "../../stores/room";
import type { SquareDTO } from "../../types/api";

const roomStore = useRoomStore();

const showCover = computed(
  () => Boolean(roomStore.room?.hide_card) && !roomStore.cardRevealed,
);

const gridStyle = computed(() => {
  const game = roomStore.game;
  if (!game) return {};
  return {
    gridTemplateColumns: `repeat(${game.cols}, 1fr)`,
    gridTemplateRows: `repeat(${game.rows}, 1fr)`,
    aspectRatio: `${game.cols} / ${game.rows}`,
  };
});

function onSquareClick(square: SquareDTO) {
  const player = roomStore.currentPlayer;
  const game = roomStore.game;
  if (!player || player.is_spectator || !game) return;

  const chosenColor = player.color;
  let remove: boolean;
  if (square.colors.length === 0) {
    remove = false;
  } else if (square.colors.includes(chosenColor)) {
    remove = true;
  } else if (game.lockout_mode !== "lockout") {
    remove = false;
  } else {
    // square is claimed by someone else and lockout mode forbids stacking
    return;
  }

  roomStore.toggleSquare(square.row, square.col, chosenColor, remove).catch((err: unknown) => {
    console.error("Failed to mark square", err);
  });
}

async function onReveal() {
  try {
    await roomStore.reveal();
  } catch (err) {
    console.error("Failed to reveal card", err);
  }
}
</script>

<template>
  <div class="board-container">
    <div class="board" :style="gridStyle">
      <div
        v-for="square in roomStore.squares"
        :key="`${square.row}-${square.col}`"
        class="square"
        :title="square.colors.join(', ')"
        :style="{ background: squareBackground(square.colors) }"
        @click="onSquareClick(square)"
      >
        <span class="goal-text">{{ square.goal }}</span>
      </div>
    </div>

    <div v-if="showCover" class="board-cover" @click="onReveal">
      <span>Click to Reveal</span>
    </div>
  </div>
</template>

<style scoped>
.board-container {
  position: relative;
}

.board {
  display: grid;
  gap: 2px;
  background: var(--border-color);
  border: 1px solid var(--border-color);
}

.square {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem;
  background-color: var(--square-bg, #1118);
  cursor: pointer;
  text-align: center;
  overflow: hidden;
}

.goal-text {
  font-size: 0.75rem;
  line-height: 1.15;
  word-break: break-word;
  text-shadow:
    0 0 3px #000,
    0 0 3px #000;
}

.board-cover {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 15, 0.92);
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  letter-spacing: 0.02em;
}
</style>
