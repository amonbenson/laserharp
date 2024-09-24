<script setup>
import { inject, computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import CameraStream from "@/components/CameraStream.vue";
import AccentButton from "@/components/AccentButton.vue";

const api = inject("api");
const laserharp = useLaserharpStore();

const targetFrameRate = computed(() => laserharp.camera?.config?.framerate ?? 0);
const actualFrameRate = computed(() => laserharp.camera?.state?.framerate ?? 0);
</script>

<template>
  <h2 class="flex justify-between items-baseline">
    <span>Camera Stream (<span :class="{ 'text-rose-500': actualFrameRate < targetFrameRate * 0.9 }">{{ actualFrameRate.toFixed() }} FPS</span>)</span>
    <AccentButton
      class="inline-block"
      @click="api.emit('app:calibrate')"
    >
      Calibrate
    </AccentButton>
  </h2>

  <div class="flex-grow flex justify-center">
    <div class="camera-stream-container">
      <CameraStream />
    </div>
  </div>
</template>

<style scoped>
.camera-stream-container {
  width: 100vh;
}
</style>
