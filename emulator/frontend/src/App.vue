<script setup>
import { ref } from "vue";
import { useEventSource } from "@vueuse/core";

const BEAM_COUNT = 15;
const BEAM_TRANSLATION_SPAN = 1.5;
const BEAM_ROTATION_SPAN = 30;

const BEAM_TRANSLATIONS = Array(BEAM_COUNT)
  .fill(null)
  .map((_, i) => (i / (BEAM_COUNT - 1) - 0.5) * BEAM_TRANSLATION_SPAN * 2);
const BEAM_ROTATIONS = Array(BEAM_COUNT)
  .fill(null)
  .map((_, i) => (i / (BEAM_COUNT - 1) - 0.5) * BEAM_ROTATION_SPAN * 2);

const beamStrengths = ref(Array(BEAM_COUNT).fill(null).map(() => 1.0));

const { status, data, error, close } = useEventSource(
  `${import.meta.env.VITE_API_ENDPOINT}/stream`,
  [],
  {
    immediate: true,
    autoReconnect: true,
  },
);

/* let interval = null;
let x = 0;
onMounted(() => {
  interval = setInterval(() => {
    x += 0.05;
    beamStrengths.value = beamStrengths.value.map((_, i) => Math.sin(i * 0.7 - x) * 0.45 + 0.5);
  }, 30);
});
onBeforeUnmount(() => {
  clearInterval(interval);
}); */
</script>

<template>
  <div class="fixed w-screen h-screen overflow-hidden flex justify-center items-center p-8">
    <div class="h-full max-w-full aspect-2/3 flex flex-col justify-stretch items-center">
      <!-- laser beams -->
      <div class="flex-1 size-full relative">
        <div
          v-for="_, i in BEAM_COUNT"
          :key="i"
          class="absolute left-1/2 top-0 w-8 h-full origin-bottom flex justify-center items-stretch"
          :style="{
            transform: `translate(-50%, 0) translate(${BEAM_TRANSLATIONS[i]}rem, 0) rotate(${BEAM_ROTATIONS[i]}deg)`,
          }"
        >
          <!-- <div
            class="w-1 h-full bg-(color:--bg-color) shadow shadow-(color:--bg-color)/50 rounded-full"
            :style="{
              opacity: `${beamStrengths[i] * 100}%`,
              '--bg-color': `hsl(from var(--color-red-500) h s calc(l - ${(1 - beamStrengths[i]) * 50}))`,
            }"
          /> -->
          <div
            class="w-1 h-full bg-red-500 shadow shadow-red-500/50 rounded-full"
            :style="{
              opacity: `${beamStrengths[i] * 100}%`,
            }"
          />
        </div>
      </div>

      <!-- harp base -->
      <div class="flex-none w-48 h-12 bg-panel rounded z-1" />
    </div>
  </div>
</template>
