<script setup>
import { computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const laserharp = useLaserharpStore();
const laserharpString = computed(() => JSON.stringify(laserharp, null, 2));
</script>

<template>
  <h2>Global State</h2>

  <pre class="bg-darker p-4 select-text">{{ laserharpString }}</pre>
</template>
