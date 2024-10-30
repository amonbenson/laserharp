<script setup>
import { computed, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import { snakeCaseToTitleCase } from "@/utils";
import TextField from "@/components/ui/TextField.vue";
import NumberField from "@/components/ui/NumberField.vue";
import ToggleSwitchField from "@/components/ui/ToggleSwitchField.vue";

const COMPONENTS = [
  "app",
  "camera",
  "image_calibrator",
  "orchestrator",
  "hwbutton",
];

const DEVELOPMENT = process.env.NODE_ENV === "development";

const api = inject("api");
const laserharp = useLaserharpStore();

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
        <!-- <input
          :id="`${componentKey}.${key}`"
          :value="value"
          :disabled="!(description.client_writable ?? true)"
          class="flex-grow w-full"
          @input="updateSetting(componentKey, key, $event.target.value)"
        > -->
        <NumberField
          v-if="['int', 'float'].includes(description.type)"
          :id="`${componentKey}.${key}`"
          :model-value="value"
          :disabled="!(description.client_writable ?? true)"
          :min="description.range[0]"
          :max="description.range[1]"
          :step="description.step ?? (description.type === 'int' ? 1 : 0.1)"
          class="flex-grow w-full"
          @update:model-value="updateSetting(componentKey, key, $event)"
        />
        <ToggleSwitchField
          v-else-if="description.type === 'bool'"
          :id="`${componentKey}.${key}`"
          :model-value="value"
          :disabled="!(description.client_writable ?? true)"
          class="flex-grow w-full"
          @update:model-value="updateSetting(componentKey, key, $event)"
        />
        <TextField
          v-else
          :id="`${componentKey}.${key}`"
          :model-value="value"
          :disabled="!(description.client_writable ?? true)"
          class="flex-grow w-full"
          @update:model-value="updateSetting(componentKey, key, $event)"
        />
      </div>
    </div>
  </div>
</template>
