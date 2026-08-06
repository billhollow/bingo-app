import { createRouter, createWebHistory } from "vue-router";

import { useSessionStore } from "../stores/session";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("../features/home/HomeView.vue"),
    },
    {
      path: "/rooms/:roomId/join",
      name: "join-room",
      component: () => import("../features/room/JoinRoomView.vue"),
      props: true,
    },
    {
      path: "/rooms/:roomId",
      name: "room",
      component: () => import("../features/room/RoomView.vue"),
      props: true,
    },
  ],
});

// A room only has state once you've joined it (create-room joins you
// automatically); visiting a bare room link with no stored session sends
// you to the join form first.
router.beforeEach((to) => {
  if (to.name === "room" && typeof to.params.roomId === "string") {
    const session = useSessionStore();
    if (!session.getSession(to.params.roomId)) {
      return { name: "join-room", params: { roomId: to.params.roomId } };
    }
  }
  return true;
});

export default router;
