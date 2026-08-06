const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function roomSocketUrl(roomId: string, token: string): string {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  return `${wsBase}/ws/rooms/${roomId}/?token=${encodeURIComponent(token)}`;
}
