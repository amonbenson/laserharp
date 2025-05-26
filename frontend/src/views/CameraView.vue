<script setup>
import { inject, computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import CameraStream from "@/components/CameraStream.vue";
import AccentButton from "@/components/ui/AccentButton.vue";
import SliderField from "@/components/ui/SliderField.vue";

const api = inject("api");
const laserharp = useLaserharpStore();

const targetFrameRate = computed(() => laserharp.camera?.config?.framerate ?? 0);
const actualFrameRate = computed(() => laserharp.camera?.state?.framerate ?? 0);

const iso = computed({
  get: () => laserharp.camera?.settings?.iso ?? 0,
  set: (value) => {
    try {
      api.updateSetting("camera", "iso", value);
    } catch (error) {
      console.error(error);
    }
  },
});

const shutterSpeed = computed({
  get: () => laserharp.camera?.settings?.shutter_speed ?? 0,
  set: (value) => {
    try {
      api.updateSetting("camera", "shutter_speed", value);
    } catch (error) {
      console.error(error);
    }
  },
});
</script>

<template>
  <div class="flex flex-col justify-center items-center space-y-2 sm:flex-row sm:justify-between sm:items-baseline sm:space-y-0">
    <h2>
      Live Stream (<span :class="{ 'text-primary-lighter': actualFrameRate < targetFrameRate * 0.9 }">{{ actualFrameRate.toFixed() }} FPS</span>)
    </h2>
    <AccentButton
      class="inline-block"
      @click="api.emit('app:calibrate')"
    >
      Calibrate
    </AccentButton>
  </div>

  <div class="flex-grow flex justify-center">
    <div class="w-[100vh]">
      <CameraStream />
    </div>
  </div>

  <h2>Camera Settings</h2>

  <div class="flex-grow flex flex-col">
    <div class="w-full flex flex-col md:flex-row justify-center items-center">
      <label
        class="flex-shrink-0 w-full md:w-1/2 truncate"
        for="camera.iso"
      >
        ISO: {{ iso }}
      </label>
      <SliderField
        v-model="iso"
        :min="laserharp.camera?.config?.settings?.iso?.range?.[0]"
        :max="laserharp.camera?.config?.settings?.iso?.range?.[1]"
        id="camera.iso"
        class="flex-grow w-full"
      />
    </div>

    <div class="w-full flex flex-col md:flex-row justify-center items-center">
      <label
        class="flex-shrink-0 w-full md:w-1/2 truncate"
        for="camera.shutterSpeed"
      >
        Shutter Speed: {{ shutterSpeed }}
      </label>
      <SliderField
        v-model="shutterSpeed"
        :min="laserharp.camera?.config?.settings?.shutter_speed?.range?.[0]"
        :max="laserharp.camera?.config?.settings?.shutter_speed?.range?.[1]"
        id="camera.shutterSpeed"
        class="flex-grow w-full"
      />
    </div>
  </div>
</template>
