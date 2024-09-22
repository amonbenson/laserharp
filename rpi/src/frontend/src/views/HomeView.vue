<script setup>
import { computed, ref, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import NoteLabel from "@/components/NoteLabel.vue";
import PedalSetting from "@/components/PedalSetting.vue";

const MAJOR_SCALE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];

const api = inject("api");
const laserharp = useLaserharpStore();

const numSections = ref(3);
const numLasers = computed(() => laserharp.laser_array?.config?.size ?? 0);
const activeArray = computed(() => laserharp.midi_converter?.state?.active?.flat() ?? []);

const midiConverterSettings = computed(() => laserharp.midi_converter?.settings);
const pedals = computed(() => Array(7).fill(null)
  .map((_, i) => MAJOR_SCALE_NOTES[i].toLocaleLowerCase())
  .map((noteName) => ({
    noteName,
    position: midiConverterSettings.value?.[`pedal_position_${noteName}`] ?? 0,
  })));

const setPedalPosition = (step, position) => {
  api.updateSetting("midi_converter", `pedal_position_${MAJOR_SCALE_NOTES[step].toLocaleLowerCase()}`, position);
};

const getX = (i) => i % numLasers.value;
const getY = (i) => Math.floor(i / numLasers.value);

const reindex = (i) => {
  const x = getX(i);
  const y = getY(i);

  // flip the y-axis
  return x + (numSections.value - 1 - y) * numLasers.value;
};
</script>

<template>
  <h2>String Sections</h2>

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
          class="h-full bg-white rounded-full transition-all duration-100"
          :class="`${activeArray[reindex(i)]
            ? 'w-2 md:w-4 lg:w-6 opacity-100'
            : 'w-1 opacity-25'
          } ${getX(i) % 7 == 0
            ? 'bg-rose-500'
            : getX(i) % 7 == 3
              ? 'bg-sky-500'
              : 'bg-white'
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
          :alteration="pedals[getX(i) % 7].position"
        />
      </div>
      <!-- eslint-enable vue/no-v-html -->
    </div>
  </div>

  <h2>Pedals</h2>

  <div class="flex justify-start sm:justify-center items-center overflow-x-auto">
    <div class="pt-2 flex space-x-8">
      <PedalSetting
        v-for="{ position }, i in pedals"
        :key="i"
        :step="i"
        :position="position"
        @update:position="setPedalPosition(i, $event)"
      />
    </div>
  </div>
</template>
