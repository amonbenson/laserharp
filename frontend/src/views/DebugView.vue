<script setup>
import { computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const laserharp = useLaserharpStore();

const keysToKeep = ["app", "ipc", "laser_array", "camera", "image_processor", "image_calibrator", "orchestrator"];
const laserharpReduced = computed(() => {
  return Object.fromEntries(
    Object.entries(laserharp).filter(([key]) => keysToKeep.includes(key)),
  );
});

const laserharpString = computed(() => JSON.stringify(laserharpReduced.value, null, 2));
</script>

<template>
  <h2>Global State</h2>

  <pre class="bg-darker p-4 select-text">{{ laserharpString }}</pre>
</template>
