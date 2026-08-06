<script setup lang="ts">
import { computed } from "vue";

import { COLOR_HEX, type PlayerColor } from "../../lib/colors";
import { useRoomStore } from "../../stores/room";

const roomStore = useRoomStore();

// Spectators and disconnected players don't get a goal-count row, matching
// bingosync's players panel.
const visiblePlayers = computed(() =>
  [...roomStore.players]
    .filter((p) => !p.is_spectator && p.connected)
    .sort((a, b) => a.name.localeCompare(b.name)),
);
</script>

<template>
  <section class="players-panel">
    <h2>Players</h2>
    <ul>
      <li v-for="player in visiblePlayers" :key="player.id">
        <span
          class="color-dot"
          :style="{ background: COLOR_HEX[player.color as PlayerColor] ?? '#999' }"
        />
        <span class="name">{{ player.name }}</span>
        <span class="counts">
          {{ roomStore.squareCountForColor(player.color) }}
          <span class="line-count">({{ roomStore.lineCountForColor(player.color) }})</span>
        </span>
      </li>
    </ul>
    <p v-if="visiblePlayers.length === 0" class="empty">No one else here yet.</p>
  </section>
</template>

<style scoped>
.players-panel h2 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.color-dot {
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 50%;
  flex-shrink: 0;
}

.name {
  flex: 1;
}

.counts {
  font-variant-numeric: tabular-nums;
  opacity: 0.85;
}

.line-count {
  opacity: 0.7;
}

.empty {
  opacity: 0.6;
  font-size: 0.85rem;
}
</style>
