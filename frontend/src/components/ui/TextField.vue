<script setup>
const model = defineModel({ type: String, required: true });
</script>

<template>
  <input v-model="model">
</template>
