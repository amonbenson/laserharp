<script setup>
import { inject, computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import CameraStream from "@/components/CameraStream.vue";
import AccentButton from "@/components/ui/AccentButton.vue";

const api = inject("api");
const laserharp = useLaserharpStore();

const targetFrameRate = computed(() => laserharp.camera?.config?.framerate ?? 0);
const actualFrameRate = computed(() => laserharp.camera?.state?.framerate ?? 0);
</script>

<template>
  <div class="flex flex-col justify-center items-center space-y-2 sm:flex-row sm:justify-between sm:items-baseline sm:space-y-0">
    <h2>
      Camera Stream (<span :class="{ 'text-primary-lighter': actualFrameRate < targetFrameRate * 0.9 }">{{ actualFrameRate.toFixed() }} FPS</span>)
    </h2>
    <AccentButton
      class="inline-block"
      @click="api.emit('app:calibrate')"
    >
      Calibrate
    </AccentButton>
  </div>

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
