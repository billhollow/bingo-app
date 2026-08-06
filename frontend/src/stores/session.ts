import { defineStore } from "pinia";
import { reactive } from "vue";

interface StoredSession {
  token: string;
  playerId: string;
}

const STORAGE_KEY = "bingo:sessions";

function loadFromStorage(): Record<string, StoredSession> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, StoredSession>) : {};
  } catch {
    return {};
  }
}

/** Per-room player identity (bearer token), persisted so a page refresh
 * doesn't kick you back to the join screen. Keyed by room id since a
 * browser may hold sessions for several rooms at once. */
export const useSessionStore = defineStore("session", () => {
  const sessions = reactive<Record<string, StoredSession>>(loadFromStorage());

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }

  function saveSession(roomId: string, session: StoredSession) {
    sessions[roomId] = session;
    persist();
  }

  function clearSession(roomId: string) {
    delete sessions[roomId];
    persist();
  }

  function getSession(roomId: string): StoredSession | undefined {
    return sessions[roomId];
  }

  return { sessions, saveSession, clearSession, getSession };
});
