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
  <div class="w-full flex justify-between items-baseline">
    <p :class="{ 'text-rose-500': actualFrameRate < targetFrameRate * 0.9 }">
      FPS: {{ actualFrameRate.toFixed() }} / {{ targetFrameRate.toFixed() }}
    </p>
    <AccentButton @click="api.emit('app:calibrate')">
      Calibrate
    </AccentButton>
  </div>

  <CameraStream class="camera-stream" />
</template>

<style scoped>
.camera-stream {
  max-width: 100vh;
}
</style>
