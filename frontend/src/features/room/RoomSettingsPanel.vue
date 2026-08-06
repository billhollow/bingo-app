<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import { errorMessage } from "../../lib/api";
import { useRoomStore } from "../../stores/room";
import type { BoardType, LockoutMode } from "../../types/api";

const roomStore = useRoomStore();

const showNewCardForm = ref(false);
const submitting = ref(false);
const error = ref("");

const form = reactive({
  goalsText: "",
  boardType: "fixed" as BoardType,
  rows: 5,
  cols: 5,
  lockoutMode: "non_lockout" as LockoutMode,
  seed: "",
  hideCard: false,
});

// Re-seed the form defaults from the live game whenever it changes, so
// opening "new card" starts from the room's current settings.
watch(
  () => roomStore.game,
  (game) => {
    if (!game) return;
    form.boardType = game.board_type;
    form.rows = game.rows;
    form.cols = game.cols;
    form.lockoutMode = game.lockout_mode;
    form.hideCard = roomStore.room?.hide_card ?? false;
  },
  { immediate: true },
);

const requiredGoalCount = computed(() => form.rows * form.cols);

function parseGoals(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await roomStore.newCard({
      goals: parseGoals(form.goalsText),
      board_type: form.boardType,
      rows: form.rows,
      cols: form.cols,
      lockout_mode: form.lockoutMode,
      seed: form.seed,
      hide_card: form.hideCard,
    });
    showNewCardForm.value = false;
    form.goalsText = "";
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="settings-panel">
    <h2>Room settings</h2>
    <dl v-if="roomStore.game" class="current-settings">
      <dt>Board</dt>
      <dd>{{ roomStore.game.rows }}×{{ roomStore.game.cols }}, {{ roomStore.game.board_type }}</dd>
      <dt>Mode</dt>
      <dd>{{ roomStore.game.lockout_mode === "lockout" ? "Lockout" : "Non-Lockout" }}</dd>
      <dt v-if="roomStore.game.seed">Seed</dt>
      <dd v-if="roomStore.game.seed">{{ roomStore.game.seed }}</dd>
    </dl>

    <button type="button" class="toggle" @click="showNewCardForm = !showNewCardForm">
      {{ showNewCardForm ? "Cancel" : "New card…" }}
    </button>

    <form v-if="showNewCardForm" class="new-card-form" @submit.prevent="onSubmit">
      <fieldset class="board-size">
        <legend>Board size</legend>
        <label>
          Rows
          <input v-model.number="form.rows" type="number" min="1" max="15" />
        </label>
        <label>
          Columns
          <input v-model.number="form.cols" type="number" min="1" max="15" />
        </label>
      </fieldset>

      <label>
        Board type
        <select v-model="form.boardType">
          <option value="fixed">Fixed ({{ requiredGoalCount }} goals)</option>
          <option value="randomized">Randomized (at least {{ requiredGoalCount }})</option>
        </select>
      </label>

      <label>
        Goals (one per line)
        <textarea v-model="form.goalsText" rows="6" required></textarea>
      </label>

      <label>
        Mode
        <select v-model="form.lockoutMode">
          <option value="non_lockout">Non-Lockout</option>
          <option value="lockout">Lockout</option>
        </select>
      </label>

      <label>
        Seed (optional)
        <input v-model="form.seed" placeholder="random" />
      </label>

      <label class="checkbox">
        <input v-model="form.hideCard" type="checkbox" />
        Hide card initially
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="submitting">
        {{ submitting ? "Generating…" : "Generate new card" }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.settings-panel h2 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
}

.current-settings {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.15rem 0.6rem;
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
}

.current-settings dt {
  opacity: 0.65;
}

.current-settings dd {
  margin: 0;
}

.toggle {
  padding: 0.35rem 0.7rem;
  border-radius: 5px;
  border: 1px solid var(--border-color, #8886);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.85rem;
}

.new-card-form {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.new-card-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-weight: 600;
  font-size: 0.85rem;
}

.new-card-form label.checkbox {
  flex-direction: row;
  align-items: center;
  font-weight: 400;
}

.board-size {
  display: flex;
  gap: 1rem;
  border: 1px solid var(--border-color, #8886);
  border-radius: 6px;
}

.board-size label {
  flex: 1;
}

input,
select,
textarea {
  padding: 0.35rem 0.5rem;
  font: inherit;
  border-radius: 4px;
  border: 1px solid var(--border-color, #8886);
}

.error {
  color: #d33;
  font-size: 0.85rem;
}

button[type="submit"] {
  align-self: flex-start;
  padding: 0.45rem 1rem;
  font-weight: 600;
  border-radius: 6px;
  border: none;
  background: #4f6df5;
  color: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
