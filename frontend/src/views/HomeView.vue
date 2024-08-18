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
    <div class="absolute inset-8">
      <CameraView />
      <div class="w-full">
        <p>Running at {{ frameRate.toFixed(1) }} FPS</p>
      </div>
    </div>
  </main>
</template>
