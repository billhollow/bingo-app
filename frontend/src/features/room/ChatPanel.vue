<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

import { useRoomStore } from "../../stores/room";
import type {
  ChatEventPayload,
  ColorEventPayload,
  ConnectionEventPayload,
  EventDTO,
  GoalEventPayload,
  NewCardEventPayload,
} from "../../types/api";

const roomStore = useRoomStore();

const messageText = ref("");
const chatBody = ref<HTMLElement | null>(null);

function describe(event: EventDTO): string {
  const name = event.player.is_spectator ? `${event.player.name} (spectator)` : event.player.name;
  switch (event.type) {
    case "chat":
      return `${name}: ${(event.payload as ChatEventPayload).text}`;
    case "goal": {
      const payload = event.payload as GoalEventPayload;
      return `${name} ${payload.remove ? "cleared" : "marked"} "${payload.goal}"`;
    }
    case "color":
      return `${name} changed color to ${(event.payload as ColorEventPayload).color}`;
    case "revealed":
      return `${name} revealed the card`;
    case "connection":
      return `${name} ${(event.payload as ConnectionEventPayload).connected ? "connected" : "disconnected"}`;
    case "new_card": {
      const payload = event.payload as NewCardEventPayload;
      return `${name} generated a new card${payload.seed ? ` (seed: ${payload.seed})` : ""}`;
    }
    default:
      return name;
  }
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

watch(
  () => roomStore.events.length,
  async () => {
    await nextTick();
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight;
  },
);

async function onSend() {
  const text = messageText.value.trim();
  if (!text) return;
  messageText.value = "";
  try {
    await roomStore.postChat(text);
  } catch (err) {
    console.error("Failed to send message", err);
  }
}
</script>

<template>
  <section class="chat-panel">
    <h2>Activity</h2>
    <div ref="chatBody" class="chat-body">
      <div v-for="(event, index) in roomStore.events" :key="index" :class="['entry', event.type]">
        <span class="time">{{ formatTime(event.created_at) }}</span>
        {{ describe(event) }}
      </div>
    </div>
    <form class="chat-input-row" @submit.prevent="onSend">
      <input v-model="messageText" placeholder="Send a message…" maxlength="2000" />
      <button type="submit">Send</button>
    </form>
  </section>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 20rem;
}

.chat-panel h2 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--border-color, #8886);
  border-radius: 6px;
  padding: 0.5rem;
  font-size: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.entry.connection,
.entry.color,
.entry.revealed,
.entry.new_card {
  opacity: 0.7;
  font-style: italic;
}

.time {
  opacity: 0.5;
  margin-right: 0.4rem;
  font-variant-numeric: tabular-nums;
}

.chat-input-row {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.4rem;
}

.chat-input-row input {
  flex: 1;
  padding: 0.4rem 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--border-color, #8886);
  font: inherit;
}

.chat-input-row button {
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  border: none;
  background: #4f6df5;
  color: white;
  cursor: pointer;
  font-weight: 600;
}
</style>
