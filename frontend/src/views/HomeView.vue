<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue";
import CameraView from "@/components/CameraView.vue";

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
      <div class="w-full">
        <p>FPS: {{ frameRate.toFixed(1) }}</p>
      </div>
      <CameraView />
    </div>
  </main>
</template>
