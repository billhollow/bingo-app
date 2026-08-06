<script setup lang="ts">
import { onMounted, ref } from "vue";

import { errorMessage } from "../../lib/api";
import { useRoomSocket } from "../../composables/useRoomSocket";
import { useRoomStore } from "../../stores/room";
import { useSessionStore } from "../../stores/session";
import BoardGrid from "./BoardGrid.vue";
import ChatPanel from "./ChatPanel.vue";
import ColorChooser from "./ColorChooser.vue";
import PlayersPanel from "./PlayersPanel.vue";
import RoomSettingsPanel from "./RoomSettingsPanel.vue";

const props = defineProps<{ roomId: string }>();

const session = useSessionStore();
const roomStore = useRoomStore();

const loading = ref(true);
const loadError = ref("");

onMounted(async () => {
  const stored = session.getSession(props.roomId);
  if (!stored) {
    // the router guard normally redirects to /join before this ever renders
    loadError.value = "You haven't joined this room yet.";
    loading.value = false;
    return;
  }

  try {
    await roomStore.load(props.roomId, stored.token, stored.playerId);
    useRoomSocket(props.roomId, stored.token, roomStore.applyEvent);
  } catch (err) {
    loadError.value = errorMessage(err);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div v-if="loading">Loading room…</div>
  <p v-else-if="loadError" class="error">{{ loadError }}</p>
  <div v-else-if="roomStore.room && roomStore.game" class="room">
    <header class="room-header">
      <h1>{{ roomStore.room.name }}</h1>
      <p class="playing-as">
        {{ roomStore.currentPlayer?.is_spectator ? "Spectating" : "Playing" }} as
        <strong>{{ roomStore.currentPlayer?.name }}</strong>
      </p>
    </header>

    <div class="room-layout">
      <section class="board-column">
        <ColorChooser />
        <BoardGrid />
      </section>
      <aside class="side-column">
        <ChatPanel />
        <PlayersPanel />
        <RoomSettingsPanel />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.room-header {
  margin-bottom: 1rem;
}

.room-header h1 {
  margin: 0 0 0.15rem;
}

.playing-as {
  margin: 0;
  opacity: 0.75;
}

.room-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(18rem, 1fr);
  gap: 1.5rem;
  align-items: start;
}

.board-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.error {
  color: #d33;
}

@media (max-width: 60rem) {
  .room-layout {
    grid-template-columns: 1fr;
  }
}
</style>
