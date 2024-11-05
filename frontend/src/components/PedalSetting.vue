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

const onPositionClick = (event) => {
  const y = event.offsetY / event.target.clientHeight;
  const position = Math.floor(y * 3) - 1;

  console.log(position);
  emit("update:position", position);
  emit("update:mute", false);
};

const onMuteClick = () => {
  emit("update:mute", !mute);
};
</script>

<template>
  <div class="flex flex-col">
    <div
      class="relative w-8 h-12"
      @click="onPositionClick"
    >
      <div class="absolute inset-0 grid grid-cols-3 grid-rows-3 -skew-x-6 pointer-events-none">
        <div class="bg-darker -m-px rounded-t" />
        <div class="" />
        <div class="" />
        <div class="bg-darker -m-px rounded-bl" />
        <div class="bg-darker -m-px rounded-tr" />
        <div class="" />
        <div class="" />
        <div class="bg-darker -m-px rounded-bl" />
        <div class="bg-darker -m-px rounded-r" />
      </div>

      <div 
        class="absolute w-5 h-5 bg-light rounded-full shadow-md shadow-light/10 transform transition-all duration-100 pointer-events-none"
        :class="{
          'left-0 top-0 translate-x-0 translate-y-0': position === -1, // flat
          'left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2': position === 0, // natural
          'left-full top-full -translate-x-full -translate-y-full': position === 1, // sharp
        }"
      />
    </div>

    <!-- <div
      class="relative mt-4 w-8 h-8"
      @click="onMuteClick"
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
