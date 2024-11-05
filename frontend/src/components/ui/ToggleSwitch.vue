<script setup>
import { watch } from "vue";

const props = defineProps({
  disabled: Boolean,
});

const model = defineModel({ type: Boolean, required: true });
</script>

<template>
  <div
    class="w-12 h-8 rounded-full px-1 py-2"
    :class="{
      'cursor-pointer': !disabled,
      'opacity-50': disabled,
    }"
    @click="!disabled && (model = !model)"
  >
    <div
      class="w-full h-full rounded-full flex justify-center items-center bg-opacity-50 shadow-inner shadow-dark/25 transition-all"
      :class="{
        'bg-white': !modelValue,
        'bg-primary': modelValue,
      }"
    >
      <input
        v-model="model"
        type="checkbox"
        class="sr-only"
      >
      <div
        class="w-6 h-6 -m-1 rounded-full shadow-md transition-all"
        :class="{
          'bg-light shadow-light/25 -translate-x-1/3': !modelValue,
          'bg-primary shadow-primary/25 translate-x-1/3': modelValue,
        }"
      />
    </div>
  </div>
</template>
