<script setup>
const model = defineModel({ type: Number, required: true });

const props = defineProps({
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  step: { type: Number, default: 1 },
});
</script>

<template>
  <input 
    v-model="model" 
    type="number" 
    :min="props.min" 
    :max="props.max" 
    :step="props.step" 
    class="border rounded-l px-2 py-1"
  >
</template>
