<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue";
import CameraView from "@/components/CameraView.vue";
import AccentButton from "@/components/AccentButton.vue";

const api = inject("api");

const frameRate = ref(0);

onMounted(() => {
  api.on("app:frame_rate", (data) => {
    frameRate.value = data;
  });
});
</script>

<template>
  <main class="w-full h-full relative">
    <div class="absolute inset-8 space-y-4">
      <div class="w-full flex justify-between items-baseline">
        <p>FPS: {{ frameRate.toFixed(1) }}</p>
        <AccentButton @click="api.emit('app:calibrate')">
          Calibrate
        </AccentButton>
      </div>
      <CameraView />
    </div>
  </main>
</template>
