<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { errorMessage } from "../../lib/api";
import { createRoom } from "../../lib/rooms-api";
import { useSessionStore } from "../../stores/session";
import type { BoardType, LockoutMode } from "../../types/api";

const router = useRouter();
const session = useSessionStore();

const form = reactive({
  name: "",
  passphrase: "",
  creatorName: "",
  goalsText: "",
  boardType: "fixed" as BoardType,
  rows: 5,
  cols: 5,
  lockoutMode: "non_lockout" as LockoutMode,
  hideCard: false,
  isSpectator: false,
});

const submitting = ref(false);
const error = ref("");

const requiredGoalCount = computed(() => form.rows * form.cols);
const parsedGoals = computed(() => parseGoals(form.goalsText));

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
    const result = await createRoom({
      name: form.name,
      passphrase: form.passphrase,
      creator_name: form.creatorName,
      goals: parsedGoals.value,
      board_type: form.boardType,
      rows: form.rows,
      cols: form.cols,
      lockout_mode: form.lockoutMode,
      hide_card: form.hideCard,
      is_spectator: form.isSpectator,
    });
    session.saveSession(result.room.id, { token: result.token, playerId: result.player.id });
    await router.push({ name: "room", params: { roomId: result.room.id } });
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="home">
    <h1>Start a new bingo room</h1>
    <form class="room-form" @submit.prevent="onSubmit">
      <label>
        Room name
        <input v-model="form.name" required maxlength="255" />
      </label>

      <label>
        Passphrase
        <input v-model="form.passphrase" type="password" required />
      </label>

      <label>
        Your nickname
        <input v-model="form.creatorName" required maxlength="50" />
      </label>

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
          <option value="fixed">Fixed ({{ requiredGoalCount }} goals, used as-is)</option>
          <option value="randomized">Randomized (drawn from a larger pool)</option>
        </select>
      </label>

      <label>
        Goals (one per line{{ form.boardType === "fixed" ? `, exactly ${requiredGoalCount}` : `, at least ${requiredGoalCount}` }})
        <textarea v-model="form.goalsText" rows="10" required></textarea>
      </label>
      <p class="goal-count">{{ parsedGoals.length }} goal(s) entered</p>

      <label>
        Mode
        <select v-model="form.lockoutMode">
          <option value="non_lockout">Non-Lockout</option>
          <option value="lockout">Lockout</option>
        </select>
      </label>

      <label class="checkbox">
        <input v-model="form.hideCard" type="checkbox" />
        Hide card initially
      </label>

      <label class="checkbox">
        <input v-model="form.isSpectator" type="checkbox" />
        Join as spectator
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="submitting">
        {{ submitting ? "Creating…" : "Create room" }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.home {
  max-width: 40rem;
  margin: 0 auto;
}

.room-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.room-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-weight: 600;
}

.room-form label.checkbox {
  flex-direction: row;
  align-items: center;
  font-weight: 400;
}

.room-form input[type="checkbox"] {
  width: auto;
}

.board-size {
  display: flex;
  gap: 1rem;
  border: 1px solid var(--border-color, #8883);
  border-radius: 6px;
}

.board-size label {
  flex: 1;
}

input,
select,
textarea {
  padding: 0.4rem 0.5rem;
  font: inherit;
  border-radius: 4px;
  border: 1px solid var(--border-color, #8886);
}

.goal-count {
  margin: -0.5rem 0 0;
  font-size: 0.85rem;
  opacity: 0.7;
}

.error {
  color: #d33;
}

button {
  align-self: flex-start;
  padding: 0.55rem 1.2rem;
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
