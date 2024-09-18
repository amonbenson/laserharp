<script setup>
import { computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const laserharp = useLaserharpStore();
const laserharpString = computed(() => JSON.stringify(laserharp, null, 2));
</script>

<template>
  <pre class="bg-gray-900 p-4 select-text">{{ laserharpString }}</pre>
</template>
