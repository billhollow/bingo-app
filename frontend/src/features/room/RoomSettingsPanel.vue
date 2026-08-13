<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import { errorMessage } from "../../lib/api";
import { LOCKOUT_MODE_LABELS, type BoardConfig } from "../../lib/board";
import { parseGoals } from "../../lib/goals";
import { useRoomStore } from "../../stores/room";
import BoardConfigFields from "./BoardConfigFields.vue";

const roomStore = useRoomStore();

const showNewCardForm = ref(false);
const submitting = ref(false);
const error = ref("");

const goalsText = ref("");
const seed = ref("");

const board = reactive<BoardConfig>({
  boardType: "fixed",
  rows: 5,
  cols: 5,
  lockoutMode: "non_lockout",
  hideCard: false,
});

// Re-seed the form defaults from the live game whenever it changes, so
// opening "new card" starts from the room's current settings.
watch(
  () => roomStore.game,
  (game) => {
    if (!game) return;
    board.boardType = game.board_type;
    board.rows = game.rows;
    board.cols = game.cols;
    board.lockoutMode = game.lockout_mode;
    board.hideCard = roomStore.room?.hide_card ?? false;
  },
  { immediate: true },
);

const requiredGoalCount = computed(() => board.rows * board.cols);
const goalParse = computed(() => parseGoals(goalsText.value));

async function onSubmit() {
  if (!goalParse.value.ok) return;

  error.value = "";
  submitting.value = true;
  try {
    await roomStore.newCard({
      goals: goalParse.value.goals,
      board_type: board.boardType,
      rows: board.rows,
      cols: board.cols,
      lockout_mode: board.lockoutMode,
      seed: seed.value,
      hide_card: board.hideCard,
    });
    showNewCardForm.value = false;
    goalsText.value = "";
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
      <dd>{{ LOCKOUT_MODE_LABELS[roomStore.game.lockout_mode] }}</dd>
      <dt v-if="roomStore.game.seed">Seed</dt>
      <dd v-if="roomStore.game.seed">{{ roomStore.game.seed }}</dd>
    </dl>

    <button type="button" class="toggle" @click="showNewCardForm = !showNewCardForm">
      {{ showNewCardForm ? "Cancel" : "New card…" }}
    </button>

    <form v-if="showNewCardForm" class="stack-form new-card-form" @submit.prevent="onSubmit">
      <BoardConfigFields v-model="board" :required-goal-count="requiredGoalCount">
        <template #goals>
          <label>
            Goals (one per line or a JSON list)
            <textarea v-model="goalsText" rows="6" required></textarea>
          </label>
          <p v-if="goalParse.ok" class="goal-count">{{ goalParse.goals.length }} goal(s) entered</p>
          <p v-else class="error">{{ goalParse.error }}</p>
        </template>
        <template #extra>
          <label>
            Seed (optional)
            <input v-model="seed" placeholder="random" />
          </label>
        </template>
      </BoardConfigFields>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" class="btn-primary" :disabled="submitting || !goalParse.ok">
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
  border: 1px solid var(--border-color);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.85rem;
}

/* The panel is a sidebar, so its copy of the shared form runs a size smaller.
 * font-size on the root is the only difference; the controls inherit it. */
.new-card-form {
  margin-top: 0.75rem;
  gap: 0.6rem;
  font-size: 0.85rem;
}
</style>
