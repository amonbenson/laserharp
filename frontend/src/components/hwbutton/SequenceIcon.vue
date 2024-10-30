<script setup>
const props = defineProps({
  sequence: {
    type: String,
    required: true,
    validator: (value) => value.match(/^[xsl]{3}$/),
  },
});
</script>

<template>
  <div class="w-24 h-8 p-3 space-x-2 flex justify-center items-center bg-darker rounded-full">
    <div
      v-for="char, i in sequence"
      :key="i"
      class="h-3 bg-light rounded-full"
      :class="{
        'hidden': char === 'x',
        'w-3 shrink-0': char === 's',
        'w-full max-w-9': char === 'l',
      }"
    />
  </div>
</template>
