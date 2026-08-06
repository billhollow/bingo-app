<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { errorMessage } from "../../lib/api";
import { joinRoom } from "../../lib/rooms-api";
import { useSessionStore } from "../../stores/session";

const props = defineProps<{ roomId: string }>();

const router = useRouter();
const session = useSessionStore();

const form = reactive({
  playerName: "",
  passphrase: "",
  isSpectator: false,
});

const submitting = ref(false);
const error = ref("");

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    const result = await joinRoom(props.roomId, {
      passphrase: form.passphrase,
      player_name: form.playerName,
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
  <div class="join">
    <h1>Join room</h1>
    <form class="join-form" @submit.prevent="onSubmit">
      <label>
        Your nickname
        <input v-model="form.playerName" required maxlength="50" />
      </label>

      <label>
        Passphrase
        <input v-model="form.passphrase" type="password" required />
      </label>

      <label class="checkbox">
        <input v-model="form.isSpectator" type="checkbox" />
        Join as spectator
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="submitting">
        {{ submitting ? "Joining…" : "Join" }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.join {
  max-width: 24rem;
  margin: 0 auto;
}

.join-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.join-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-weight: 600;
}

.join-form label.checkbox {
  flex-direction: row;
  align-items: center;
  font-weight: 400;
}

input[type="checkbox"] {
  width: auto;
}

input {
  padding: 0.4rem 0.5rem;
  font: inherit;
  border-radius: 4px;
  border: 1px solid var(--border-color, #8886);
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
