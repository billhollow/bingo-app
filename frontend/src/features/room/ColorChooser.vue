<script setup lang="ts">
import { COLOR_HEX, PLAYER_COLORS, type PlayerColor } from "../../lib/colors";
import { useRoomStore } from "../../stores/room";

const roomStore = useRoomStore();

async function choose(color: PlayerColor) {
  if (roomStore.currentPlayer?.color === color) return;
  try {
    await roomStore.setColor(color);
  } catch (err) {
    console.error("Failed to change color", err);
  }
}
</script>

<template>
  <div v-if="!roomStore.currentPlayer?.is_spectator" class="color-chooser">
    <button
      v-for="color in PLAYER_COLORS"
      :key="color"
      type="button"
      class="swatch"
      :class="{ chosen: roomStore.currentPlayer?.color === color }"
      :style="{ background: COLOR_HEX[color] }"
      :aria-label="color"
      @click="choose(color)"
    />
  </div>
</template>

<style scoped>
.color-chooser {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.swatch {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
}

.swatch.chosen {
  border-color: var(--fg-color, #fff);
  box-shadow: 0 0 0 2px #0008;
}
</style>
