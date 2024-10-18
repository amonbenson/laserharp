<script setup>
import { computed, watch, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const COMPONENTS = [
  "app",
  "camera",
  "image_calibrator",
  "midi_converter",
];

const DEVELOPMENT = process.env.NODE_ENV === "development";

const api = inject("api");
const laserharp = useLaserharpStore();

const snakeCaseToTitleCase = (str) => str.split("_").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");

const componentSettings = computed(() => COMPONENTS
  .map((componentKey) => ({
    componentKey,
    componentName: snakeCaseToTitleCase(componentKey),
    settings: Object
      .entries(laserharp[componentKey]?.config?.settings ?? {})
      .map(([key, description]) => ({
        key,
        name: snakeCaseToTitleCase(key),
        value: laserharp[componentKey]?.settings[key],
        description,
      }))
      .filter(({ description }) => (description.client_writable ?? true) || DEVELOPMENT),
  }))
  .filter(({ settings }) => settings.length > 0));

const updateSetting = (componentKey, key, value) => {
  try {
    api.updateSetting(componentKey, key, value);
  } catch (error) {
    console.error(error);
  }
};
</script>

<template>
  <div
    v-for="{ componentKey, componentName, settings } in componentSettings"
    :key="componentKey"
  >
    <h2 class="truncate">
      {{ componentName }}
    </h2>
    <div class="space-y-2">
      <div
        v-for="{ key, name, value, description } in settings"
        :key="key"
        class="w-full flex flex-col md:flex-row justify-center items-center"
      >
        <label
          class="flex-shrink-0 w-full md:w-1/2 truncate"
          :for="`${componentKey}.${key}`"
        >
          {{ name }}
        </label>
        <input
          :id="`${componentKey}.${key}`"
          :value="value"
          :disabled="!(description.client_writable ?? true)"
          class="flex-grow w-full"
          @input="updateSetting(componentKey, key, $event.target.value)"
        >
      </div>
    </div>
  </div>
</template>
