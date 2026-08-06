<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div id="app-shell">
    <header class="app-header">
      <RouterLink to="/" class="app-title">Bingo</RouterLink>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--border-color, #3333);
}

.app-title {
  font-weight: 700;
  font-size: 1.1rem;
  text-decoration: none;
  color: inherit;
}

.app-main {
  padding: 1.25rem;
}
</style>
