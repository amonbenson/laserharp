<script setup>
import { computed } from "vue";

const MAJOR_SCALE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];

const props = defineProps({
  step: { type: Number, required: true },
  alteration: { type: Number, required: true },
});

const scaleIndex = computed(() => props.step % 7);
const label = computed(() => MAJOR_SCALE_NOTES[scaleIndex.value]);
const isC = computed(() => scaleIndex.value === 0);
const isF = computed(() => scaleIndex.value === 3);
</script>

<template>
  <span
    class="truncate"
    :class="isC
      ? 'text-rose-500'
      : isF
        ? 'text-sky-500'
        : 'text-white'"
  >
    {{ label }}<template v-if="props.alteration === -1">&flat;</template><template v-else-if="props.alteration === 1">&sharp;</template>
  </span>
</template>
