import { API_BASE_URL } from "./api";

export const roomSocketUrl = (roomId: string, token: string): string => {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  return `${wsBase}/ws/rooms/${roomId}/?token=${encodeURIComponent(token)}`;
};
