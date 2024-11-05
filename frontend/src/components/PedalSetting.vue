<script setup>
import NoteLabel from "@/components/NoteLabel.vue";

const props = defineProps({
  step: { type: Number, required: true },
});

const emit = defineEmits(["update:position", "update:mute"]);

const position = defineModel("position", { type: Number, required: true });
const mute = defineModel("mute", { type: Boolean, required: true });

const onPositionClick = (event) => {
  if (props.mute) {
    return;
  }

  const y = event.offsetY / event.target.clientHeight;
  const position = Math.floor(y * 3) - 1;

  emit("update:position", position);
  emit("update:mute", false);
};

const onMuteClick = () => {
  emit("update:mute", !props.mute);
};
</script>

<template>
  <div class="flex flex-col space-y-4">
    <div
      class="relative w-8 h-12"
      :class="{
        'opacity-50': props.mute,
      }"
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
        class="absolute w-5 h-5 bg-light rounded-full shadow-md shadow-light/10 transition-all duration-100 pointer-events-none"
        :class="{
          'left-0 top-0 translate-x-0 translate-y-0': props.position === -1, // flat
          'left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2': props.position === 0, // natural
          'left-full top-full -translate-x-full -translate-y-full': props.position === 1, // sharp
        }"
      />
    </div>

    <div
      class="w-8 h-8 rounded flex justify-center items-center hover:bg-danger/50 cursor-pointer transition-all"
      :class="{
        'bg-danger/50': props.mute,
      }"
      @click="onMuteClick"
    >
      <NoteLabel
        :step="props.step"
        :alteration="props.position"
      />
    </div>
  </div>
</template>
