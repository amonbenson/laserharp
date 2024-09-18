<script setup>
import { computed, ref } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const MAJOR_SCALE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];
const ALTERATIONS = ["&flat;", "", "&sharp;"];

const laserharp = useLaserharpStore();

const numSections = ref(3);
const numLasers = computed(() => laserharp.laser_array?.config?.size ?? 0);
const activeArray = computed(() => laserharp.midi_converter?.state?.active?.flat() ?? []);

const midiConverterSettings = computed(() => laserharp.midi_converter?.settings);
const pedalPositions = computed(() => Array(7).fill(null)
  .map((_, i) => MAJOR_SCALE_NOTES[i].toLocaleLowerCase())
  .map((noteName) => midiConverterSettings.value[`pedal_position_${noteName}`]));

const noteLabels = computed(() => Array(numLasers.value).fill(null).map((_, i) => {
  const name = MAJOR_SCALE_NOTES[i % 7];
  const alteration = ALTERATIONS[pedalPositions.value[i % 7] + 1];
  return `${name}${alteration}`;
}));

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
  <div>
    <div
      class="aspect-[2/1] grid gap-1"
      :style="{
        gridTemplateRows: `repeat(${numSections}, 1fr) auto`,
        gridTemplateColumns: `repeat(${numLasers}, 1fr)`,
      }"
    >
      <div
        v-for="_, i in (numSections * numLasers)"
        :key="i"
        class="flex justify-center items-center overflow-hidden"
      >
        <div
          class="h-full bg-white rounded-full transition-all duration-300"
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
        v-for="label, i in noteLabels"
        :key="i"
        class="pt-2 flex justify-center items-center"
        :class="getX(i) % 7 == 0
          ? 'text-rose-500'
          : getX(i) % 7 == 3
            ? 'text-sky-500'
            : 'text-white'"
        v-html="label"
      />
      <!-- eslint-enable vue/no-v-html -->
    </div>
  </div>
</template>
