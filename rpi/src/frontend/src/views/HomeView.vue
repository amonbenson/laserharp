<script setup>
import { onMounted, onBeforeUnmount, inject, computed } from "vue";
import { storeToRefs } from "pinia";
import { useLaserharpStore } from "@/stores/laserharp";
import CameraView from "@/components/CameraView.vue";
import AccentButton from "@/components/AccentButton.vue";

const api = inject("api");
const laserharp = useLaserharpStore();

const targetFrameRate = computed(() => laserharp.camera?.config?.framerate ?? 0);
const actualFrameRate = computed(() => laserharp.camera?.state?.frame_rate ?? 0);

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
        <p :class="{ 'text-rose-500': actualFrameRate < targetFrameRate * 0.9 }">
          FPS: {{ actualFrameRate.toFixed() }}
        </p>
        <AccentButton @click="api.emit('app:calibrate')">
          Calibrate
        </AccentButton>
      </div>
      <CameraView />
    </div>
  </main>
</template>
