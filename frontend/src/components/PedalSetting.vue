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
      <div class="absolute left-0 bottom-0 w-1/3 h-1/2 bg-darker" />
    </div>
    <div
      class="w-8 h-8 bg-darker flex justify-center items-center"
      @click="emit('update:position', 0), emit('update:mute', false)"
    >
      <div 
        class="bg-light w-3/4 h-3/4 rounded-full z-10 transform transition-transform duration-100"
        :class="{
          'translate-x-1/2 translate-y-full': position === -1,
          '-translate-x-1/2 -translate-y-full': position === 1,
        }"
      />
    </div>
    <div
      class="relative w-8 h-8"
      @click="emit('update:position', position === -1 ? 0 : -1), emit('update:mute', false)"
    >
      <div class="absolute right-0 top-0 w-1/3 h-1/2 bg-darker" />
    </div>

    <!-- <div
      class="relative mt-4 w-8 h-8"
      @click="emit('update:mute', !mute)"
    >
      <span
        class="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 text-xl"
        :class="mute ? 'text-error' : 'text-muted'"
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
