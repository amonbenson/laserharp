<script setup>
import NoteLabel from "@/components/NoteLabel.vue";

const props = defineProps({
  step: { type: Number, required: true },
  position: { type: Number, default: 0 },
  mute: { type: Boolean, default: false },
});

const emit = defineEmits([
  "update:position",
  "update:mute",
]);
</script>

<template>
  <div class="flex flex-col">
    <div
      class="relative w-8 h-8"
      @click="emit('update:position', position === 1 ? 0 : 1), emit('update:mute', false)"
    >
      <div class="absolute left-0 top-0 w-1/3 h-full bg-gray-900" />
      <div
        v-if="position === 1"
        class="absolute left-1/2 top-1/2 transform -translate-x-full -translate-y-3/4 w-6 h-6 bg-white rounded-full"
      />
    </div>
    <div
      class="relative w-8 h-8 bg-gray-900"
      @click="emit('update:position', 0), emit('update:mute', false)"
    >
      <div 
        v-if="position === 0"
        class="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-white rounded-full"
      />
    </div>
    <div
      class="relative w-8 h-8"
      @click="emit('update:position', position === -1 ? 0 : -1), emit('update:mute', false)"
    >
      <div class="absolute right-0 top-0 w-1/3 h-full bg-gray-900" />
      <div 
        v-if="position === -1"
        class="absolute left-1/2 top-1/2 transform -translate-y-1/4 w-6 h-6 bg-white rounded-full"
      />
    </div>

    <!-- <div
      class="relative mt-4 w-8 h-8"
      @click="emit('update:mute', !mute)"
    >
      <span
        class="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 text-xl"
        :class="mute ? 'text-rose-600' : 'text-gray-500'"
      >&cross;</span>
    </div> -->

    <div class="w-8 h-8 mt-4 flex justify-center items-center">
      <NoteLabel
        :step="step"
        :alteration="position"
      />
    </div>
  </div>
</template>
