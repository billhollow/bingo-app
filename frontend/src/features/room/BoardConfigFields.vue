<script setup lang="ts">
import { LOCKOUT_MODE_LABELS, type BoardConfig } from "../../lib/board";

/** The board settings "create room" and "new card" both ask for.
 *
 * The parent owns the reactive config object and binds it with v-model; the
 * goals textarea differs between the two forms, so it comes in as a slot. */
const form = defineModel<BoardConfig>({ required: true });

defineProps<{
  /** Goals needed at the current size - shown in the board-type labels. */
  requiredGoalCount: number;
}>();
</script>

<template>
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
      <option value="fixed">Fixed (exactly {{ requiredGoalCount }} goals, used as-is)</option>
      <option value="randomized">Randomized (at least {{ requiredGoalCount }}, drawn from the pool)</option>
    </select>
  </label>

  <slot name="goals" />

  <label>
    Mode
    <select v-model="form.lockoutMode">
      <option value="non_lockout">{{ LOCKOUT_MODE_LABELS.non_lockout }}</option>
      <option value="lockout">{{ LOCKOUT_MODE_LABELS.lockout }}</option>
    </select>
  </label>

  <slot name="extra" />

  <label class="checkbox">
    <input v-model="form.hideCard" type="checkbox" />
    Hide card initially
  </label>
</template>
