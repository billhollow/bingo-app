<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { errorMessage } from "../../lib/api";
import type { BoardConfig } from "../../lib/board";
import { parseGoals } from "../../lib/goals";
import { createRoom } from "../../lib/rooms-api";
import { useSessionStore } from "../../stores/session";
import BoardConfigFields from "../room/BoardConfigFields.vue";

const router = useRouter();
const session = useSessionStore();

const form = reactive({
  name: "",
  passphrase: "",
  creatorName: "",
  goalsText: "",
  isSpectator: false,
});

const board = reactive<BoardConfig>({
  boardType: "fixed",
  rows: 5,
  cols: 5,
  lockoutMode: "non_lockout",
  hideCard: false,
});

const submitting = ref(false);
const error = ref("");

const requiredGoalCount = computed(() => board.rows * board.cols);
const goalParse = computed(() => parseGoals(form.goalsText));

async function onSubmit() {
  if (!goalParse.value.ok) return;

  error.value = "";
  submitting.value = true;
  try {
    const result = await createRoom({
      name: form.name,
      passphrase: form.passphrase,
      creator_name: form.creatorName,
      goals: goalParse.value.goals,
      board_type: board.boardType,
      rows: board.rows,
      cols: board.cols,
      lockout_mode: board.lockoutMode,
      hide_card: board.hideCard,
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
    <form class="stack-form" @submit.prevent="onSubmit">
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

      <BoardConfigFields v-model="board" :required-goal-count="requiredGoalCount">
        <template #goals>
          <label>
            Goals (one per line or a JSON list{{
              board.boardType === "fixed" ? `, exactly ${requiredGoalCount}` : `, at least ${requiredGoalCount}`
            }})
            <textarea v-model="form.goalsText" rows="10" required></textarea>
          </label>
          <p v-if="goalParse.ok" class="goal-count">{{ goalParse.goals.length }} goal(s) entered</p>
          <p v-else class="error">{{ goalParse.error }}</p>
        </template>
      </BoardConfigFields>

      <label class="checkbox">
        <input v-model="form.isSpectator" type="checkbox" />
        Join as spectator
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" class="btn-primary" :disabled="submitting || !goalParse.ok">
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
</style>
