<script setup>
import { computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const COMPONENTS = [
  "midi_converter",
];

const laserharp = useLaserharpStore();

const snakeCaseToTitleCase = (str) => str.split("_").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");

const componentSettings = computed(() => COMPONENTS.map((componentKey) => ({
  componentKey,
  componentName: snakeCaseToTitleCase(componentKey),
  settings: Object.entries(laserharp[componentKey]?.config.settings ?? {}).map(([key, description]) => ({
    key,
    name: snakeCaseToTitleCase(key),
    ...description,
    value: laserharp[componentKey]?.settings[key],
  })),
})));

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
        v-for="{ key, name, ...data } in settings"
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
          :value="data.value"
          class="flex-grow w-full px-4 py-1 bg-gray-900"
          @input="console.log($event)"
        >
      </div>
    </div>
  </div>
</template>
