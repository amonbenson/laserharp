<script setup>
import { computed, ref, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import BigToggleButton from "@/components/ui/BigToggleButton.vue";
import NoteLabel from "@/components/NoteLabel.vue";
import PedalSetting from "@/components/PedalSetting.vue";
import SequenceSelector from "@/components/hwbutton/SequenceSelector.vue";

const api = inject("api");
const laserharp = useLaserharpStore();

const numSections = ref(3);
const numLasers = computed(() => laserharp.laser_array?.config?.size ?? 0);
const activeArray = computed(() => laserharp.orchestrator?.state?.active?.flat() ?? []);

const midiConverterSettings = computed(() => laserharp.orchestrator?.settings);
const pedalPositions = computed(() => Array(7).fill(null)
  .map((_, step) => midiConverterSettings.value?.[`pedal_position_${step}`] ?? 0));

const setPedalPosition = (step, position) => {
  api.updateSetting("orchestrator", `pedal_position_${step}`, position);
};

const getX = (i) => i % numLasers.value;
const getY = (i) => Math.floor(i / numLasers.value);

const reindex = (i) => {
  const x = getX(i);
  const y = getY(i);

  // flip the y-axis
  return x + (numSections.value - 1 - y) * numLasers.value;
};

const hwbuttonActions = computed(() => Object.fromEntries(Object
  .entries(laserharp?.hwbutton?.settings ?? {})
  .filter(([key]) => key.startsWith("sequence_"))
  .map(([key, value]) => ([key.replace("sequence_", ""), value]))));
</script>

<template>
  <h2>Quick Actions</h2>

  <div class="flex justify-center items-center">
    <div class="flex space-x-4">
      <BigToggleButton
        label="Flip Harp"
        active-description="Audience View"
        inactive-description="Performer View"
        :model-value="laserharp.orchestrator?.settings?.flipped"
        @update:model-value="api.updateSetting('orchestrator', 'flipped', $event)"
      />

      <BigToggleButton
        label="Calibrate"
        active-description="Calibrating..."
        inactive-description="Ready"
        :disabled="laserharp?.app?.state?.status === 'calibrating'"
        :model-value="laserharp?.app?.state?.status === 'calibrating'"
        @update:model-value="api.emit('app:calibrate')"
      />
    </div>
  </div>

  <h2>Strings</h2>

  <div class="flex justify-start sm:justify-center items-center overflow-x-auto">
    <div
      class="min-h-64 w-full lg:w-2/3 aspect-[2/1] grid gap-1"
      :style="{
        gridTemplateRows: `repeat(${numSections}, 1fr) auto`,
        gridTemplateColumns: `repeat(${numLasers}, 1fr)`,
      }"
    >
      <div
        v-for="_, i in (numSections * numLasers)"
        :key="i"
        class="min-w-8 flex justify-center items-center overflow-hidden"
      >
        <div
          class="h-full bg-light rounded-full transition-all duration-100"
          :class="`${activeArray[reindex(i)]
            ? 'w-2 md:w-4 lg:w-6 opacity-100'
            : 'w-1 opacity-25'
          } ${getX(i) % 7 == 0
            ? 'bg-primary'
            : getX(i) % 7 == 3
              ? 'bg-secondary'
              : 'bg-light'
          }`"
        />
      </div>

      <!-- eslint-disable vue/no-v-html -->
      <div
        v-for="_, i in numLasers"
        :key="i"
        class="pt-2 flex justify-center items-center"
      >
        <NoteLabel
          :step="getX(i)"
          :alteration="pedalPositions[getX(i) % 7]"
        />
      </div>
      <!-- eslint-enable vue/no-v-html -->
    </div>
  </div>

  <h2>Pedals</h2>

  <div class="flex justify-start sm:justify-center items-center overflow-x-auto">
    <div class="pt-2 flex space-x-8">
      <PedalSetting
        v-for="position, i in pedalPositions"
        :key="i"
        :step="i"
        :position="position"
        @update:position="setPedalPosition(i, $event)"
      />
    </div>
  </div>

  <h2>Button Assignment</h2>

  <div class="flex justify-center items-center">
    <div class="w-full sm:w-96 flex flex-col space-y-2">
      <SequenceSelector
        v-for="value, key in hwbuttonActions"
        :key="key"
        :sequence="key"
        :model-value="value"
        @update:model-value="api.updateSetting('hwbutton', `sequence_${key}`, $event)"
      />
    </div>
  </div>
</template>
