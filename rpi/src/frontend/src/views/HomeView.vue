<script setup>
import { computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const laserharp = useLaserharpStore();
const laserharpString = computed(() => JSON.stringify(laserharp, null, 2));
</script>

<template>
  <div>
    Hello
  </div>
</template>
