<script setup>
import ToggelSwitch from "@/components/ui/ToggleSwitch.vue";

const props = defineProps({
  disabled: Boolean,
});

const model = defineModel({ type: Boolean, required: true });
</script>

<template>
  <div
    class="flex justify-start items-center"
    :class="{
      'cursor-pointer': !disabled
    }"
    @click="!disabled && (model = !model)"
  >
    <ToggelSwitch
      v-bind="$props"
      :model-value="model"
    />
  </div>
</template>
