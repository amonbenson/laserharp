<script setup>
const props = defineProps({
  title: { type: String, default: "" },
});
</script>

<template>
  <h2 v-if="title">
    {{ props.title }}
  </h2>

  <div class="flex justify-start sm:justify-center items-center overflow-x-auto">
    <slot />
  </div>
</template>
