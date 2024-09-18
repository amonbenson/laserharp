<script setup>
import { computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const laserharp = useLaserharpStore();
const laserharpString = computed(() => JSON.stringify(laserharp, null, 2));
</script>

<template>
  <main class="w-full h-full relative overflow-y-auto">
    <pre class="absolute inset-8 space-y-4 select-text">{{ laserharpString }}</pre>
  </main>
</template>
