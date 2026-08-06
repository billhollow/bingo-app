import { onBeforeUnmount, ref } from "vue";

import { roomSocketUrl } from "../lib/ws";
import type { EventDTO } from "../types/api";

const RECONNECT_DELAY_MS = 2000;

export type SocketStatus = "connecting" | "open" | "closed";

/** Owns one websocket connection for the room's lifetime, reconnecting on
 * drop. All state mutation happens via `onEvent`; this composable never
 * touches the store directly, so it stays trivially testable/replaceable. */
export function useRoomSocket(roomId: string, token: string, onEvent: (event: EventDTO) => void) {
  const status = ref<SocketStatus>("connecting");
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let closedByCaller = false;

  function connect() {
    status.value = "connecting";
    socket = new WebSocket(roomSocketUrl(roomId, token));

    socket.onopen = () => {
      status.value = "open";
    };

    socket.onmessage = (evt: MessageEvent<string>) => {
      const data = JSON.parse(evt.data) as EventDTO;
      onEvent(data);
    };

    socket.onclose = () => {
      status.value = "closed";
      if (!closedByCaller) {
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      }
    };

    socket.onerror = () => {
      socket?.close();
    };
  }

  function disconnect() {
    closedByCaller = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    socket?.close();
  }

  connect();
  onBeforeUnmount(disconnect);

  return { status, disconnect };
}
