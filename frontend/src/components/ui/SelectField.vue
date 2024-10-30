<script setup>
const props = defineProps({
  options: {
    type: Object,
    required: true,
  },
});

const model = defineModel({ type: String, defaultValue: "" });
</script>

<template>
  <select v-model="model">
    <option
      v-for="value, key in options"
      :key="key"
      :value="key"
    >
      {{ value }}
    </option>
  </select>
</template>

<style scoped>
</style>
