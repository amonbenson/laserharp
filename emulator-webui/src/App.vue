<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useTopic } from "./composables/mqtt";

const LASER_TRANSLATION_SPAN = 1.5;
const LASER_ROTATION_SPAN = 30;

const laserBrightnesses = useTopic("lh/emulator/lasers/brightnesses", { default: [] });
const laserCount = computed(() => laserBrightnesses.value?.length ?? 0);

const laserIntersections = useTopic("lh/emulator/lasers/intersections", { default: [] });
watch(laserCount, (count) => {
  laserIntersections.value = Array(count).fill(null);
});

const laserTransforms = computed(() => Array(laserCount.value)
  .fill(null)
  .map((_, i) => laserCount.value > 1 ? (i / (laserCount.value - 1) - 0.5) * 2 : 0)
  .map((x) => ({
    translateX: x * LASER_TRANSLATION_SPAN,
    rotate: x * LASER_ROTATION_SPAN,
  })));

const cursor = ref(null);
function handleMouseMove(event) {
  cursor.value.style.left = `${event.clientX}px`;
  cursor.value.style.top = `${event.clientY}px`;
}
onMounted(() => {
  window.addEventListener("mousemove", handleMouseMove);
  window.addEventListener("mousedown", handleMouseMove);
});
onBeforeUnmount(() => {
  window.removeEventListener("mousemove", handleMouseMove);
  window.removeEventListener("mousedown", handleMouseMove);
});

function onBeamIntersect(index, event) {
  if (event.buttons === 1) {
    const y = 1.0 - event.layerY / event.target.clientHeight;
    laserIntersections.value[index] = y;
  } else {
    laserIntersections.value[index] = null;
  }
}

function onBeamLeave(index) {
  laserIntersections.value[index] = null;
}
</script>

<template>
  <div class="fixed left-0 top-0 w-screen h-screen overflow-hidden flex justify-center items-center p-8">
    <div class="h-full max-w-full aspect-2/3 flex flex-col justify-stretch items-center">
      <!-- laser beams -->
      <div class="flex-1 size-full relative">
        <div
          v-for="_, i in laserCount"
          :key="i"
          class="absolute left-1/2 top-0 w-12 h-full origin-bottom flex justify-center items-stretch"
          :style="{
            transform: `translate(-50%, 0.1rem) translate(${laserTransforms[i].translateX}rem, 0) rotate(${laserTransforms[i].rotate}deg)`,
          }"
          @mousedown="onBeamIntersect(i, $event)"
          @mousemove="onBeamIntersect(i, $event)"
          @mouseup="onBeamLeave(i)"
          @mouseleave="onBeamLeave(i)"
        >
          <div
            class="w-1 h-full bg-red-500 shadow shadow-red-500/50 rounded-full origin-bottom pointer-events-none"
            :style="{
              opacity: `${laserBrightnesses[i] * 100}%`,
              transform: `scale(1.0, ${laserIntersections[i] ?? 1.0})`
            }"
          />
        </div>
      </div>

      <!-- harp base -->
      <div class="flex-none w-48 h-12 bg-panel rounded z-1" />
    </div>
  </div>

  <div class="fixed left-0 top-0 w-screen h-screen overflow-hidden pointer-events-none">
    <div
      ref="cursor"
      class="absolute size-12 bg-dark border-3 border-panel rounded-full -translate-1/2 pointer-events-none"
    />
  </div>
</template>
