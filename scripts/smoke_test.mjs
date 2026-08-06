#!/usr/bin/env node
// Manual end-to-end smoke test against a *running* backend (both the REST
// API and the Channels websocket layer). Not part of the automated test
// suite (Django's `manage.py test rooms` covers the same behavior against
// an in-process app) - this exercises the real network path a browser
// client actually uses, which is how the URL-encoded-token websocket auth
// bug got caught (see docs/BUILD_REPORT.md).
//
// Usage:
//   cd backend && python manage.py runserver 8000   # in one terminal
//   node scripts/smoke_test.mjs                      # in another

const BASE = process.env.SMOKE_TEST_BASE_URL ?? "http://localhost:8000";
const WS_BASE = BASE.replace(/^http/, "ws");

let failures = 0;

function ok(cond, label) {
  if (cond) {
    console.log(`  ok - ${label}`);
  } else {
    console.error(`  FAIL - ${label}`);
    failures++;
  }
}

async function post(path, body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: JSON.stringify(body) });
  const data = await res.json().catch(() => null);
  return { status: res.status, data };
}

async function get(path, token) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { headers });
  const data = await res.json().catch(() => null);
  return { status: res.status, data };
}

function openSocket(roomId, token) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`${WS_BASE}/ws/rooms/${roomId}/?token=${encodeURIComponent(token)}`);
    const messages = [];
    ws.addEventListener("message", (evt) => messages.push(JSON.parse(evt.data)));
    ws.addEventListener("open", () => resolve({ ws, messages }));
    ws.addEventListener("error", reject);
  });
}

function waitForMessage(messages, predicate, timeoutMs = 3000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const interval = setInterval(() => {
      const found = messages.find(predicate);
      if (found) {
        clearInterval(interval);
        resolve(found);
      } else if (Date.now() - start > timeoutMs) {
        clearInterval(interval);
        reject(new Error("timed out waiting for message: " + JSON.stringify(messages)));
      }
    }, 50);
  });
}

async function main() {
  console.log("1. create room (lockout mode, 3x3 board)");
  const goals = Array.from({ length: 9 }, (_, i) => `goal ${i}`);
  const created = await post("/api/rooms/", {
    name: "Smoke Test Room",
    passphrase: "hunter2",
    creator_name: "Alice",
    goals,
    rows: 3,
    cols: 3,
    lockout_mode: "lockout",
  });
  ok(created.status === 201, `create room -> 201 (got ${created.status})`);
  const roomId = created.data.room.id;
  const aliceToken = created.data.token;

  console.log("2. join room as Bob");
  const joined = await post(`/api/rooms/${roomId}/join/`, {
    passphrase: "hunter2",
    player_name: "Bob",
  });
  ok(joined.status === 201, `join room -> 201 (got ${joined.status})`);
  const bobToken = joined.data.token;

  console.log("3. wrong passphrase rejected");
  const badJoin = await post(`/api/rooms/${roomId}/join/`, { passphrase: "nope", player_name: "Eve" });
  ok(badJoin.status === 403, `wrong passphrase -> 403 (got ${badJoin.status})`);

  console.log("4. fetch board (9 squares) and players (2)");
  const board = await get(`/api/rooms/${roomId}/board/`, aliceToken);
  ok(board.status === 200 && board.data.length === 9, `board has 9 squares (got ${board.data?.length})`);
  const players = await get(`/api/rooms/${roomId}/players/`, aliceToken);
  ok(players.status === 200 && players.data.length === 2, `2 players (got ${players.data?.length})`);

  console.log("5. open websockets for both players");
  const alice = await openSocket(roomId, aliceToken);
  const bob = await openSocket(roomId, bobToken);
  await waitForMessage(alice.messages, (m) => m.type === "connection"); // alice's own connect
  await waitForMessage(bob.messages, (m) => m.type === "connection"); // bob's own connect, seen by bob
  await waitForMessage(alice.messages, (m) => m.type === "connection" && m.player.name === "Bob");
  ok(true, "both sockets connected and see each others' connection events");

  console.log("6. alice marks a square, bob sees it over the socket");
  const mark = await post(`/api/rooms/${roomId}/goal/`, { row: 0, col: 0, color: "red" }, aliceToken);
  ok(mark.status === 201, `mark square -> 201 (got ${mark.status})`);
  const bobSawGoal = await waitForMessage(bob.messages, (m) => m.type === "goal");
  ok(
    bobSawGoal.payload.row === 0 && bobSawGoal.payload.colors.includes("red"),
    "bob received alice's goal event over the socket",
  );

  console.log("7. lockout mode blocks bob from claiming alice's square");
  const blocked = await post(`/api/rooms/${roomId}/goal/`, { row: 0, col: 0, color: "blue" }, bobToken);
  ok(blocked.status === 409, `lockout conflict -> 409 (got ${blocked.status})`);

  console.log("8. chat message is broadcast");
  const chat = await post(`/api/rooms/${roomId}/chat/`, { text: "gl hf" }, aliceToken);
  ok(chat.status === 201, `chat -> 201 (got ${chat.status})`);
  const bobSawChat = await waitForMessage(bob.messages, (m) => m.type === "chat");
  ok(bobSawChat.payload.text === "gl hf", "bob received alice's chat message");

  console.log("9. new card regenerates the board (2x2 this time)");
  const newCardGoals = ["a", "b", "c", "d"];
  const newCard = await post(
    `/api/rooms/${roomId}/new-card/`,
    { goals: newCardGoals, rows: 2, cols: 2 },
    aliceToken,
  );
  ok(newCard.status === 201, `new card -> 201 (got ${newCard.status})`);
  const boardAfter = await get(`/api/rooms/${roomId}/board/`, aliceToken);
  ok(boardAfter.data.length === 4, `board resized to 4 squares (got ${boardAfter.data?.length})`);
  await waitForMessage(bob.messages, (m) => m.type === "new_card");
  ok(true, "bob received the new_card broadcast");

  console.log("10. feed replay includes full history in order");
  const feed = await get(`/api/rooms/${roomId}/feed/`, aliceToken);
  const types = feed.data.map((e) => e.type);
  ok(
    types.includes("goal") && types.includes("chat") && types.includes("new_card"),
    `feed includes goal/chat/new_card (got ${JSON.stringify(types)})`,
  );

  console.log("11. disconnecting alice's socket broadcasts a disconnect to bob");
  alice.ws.close();
  const bobSawDisconnect = await waitForMessage(
    bob.messages,
    (m) => m.type === "connection" && m.player.name === "Alice" && m.payload.connected === false,
  );
  ok(!bobSawDisconnect.payload.connected, "bob saw alice's disconnect event");

  bob.ws.close();

  console.log(`\n${failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"}`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error("Smoke test crashed:", err);
  process.exit(1);
});
