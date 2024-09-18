<script setup>
import { computed, ref } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const MAJOR_SCALE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];

const laserharp = useLaserharpStore();

const numSections = ref(3);
const numLasers = computed(() => laserharp.laser_array?.config?.size ?? 0);
const activeArray = computed(() => laserharp.midi_converter?.state?.active?.flat() ?? []);

const reindex = (i) => {
  const x = i % numLasers.value;
  const y = Math.floor(i / numLasers.value);

  // flip the y-axis
  return x + (numSections.value - 1 - y) * numLasers.value;
};
</script>

<template>
  <p>{{ numSections }} {{ numLasers }}</p>
  <div>
    <div
      class="aspect-[2/1] grid gap-1"
      :style="{
        gridTemplateRows: `repeat(${numSections}, 1fr) auto`,
        gridTemplateColumns: `repeat(${numLasers}, 1fr)`,
      }"
    >
      <div
        v-for="i in (numSections * numLasers)"
        :key="i"
        class="flex justify-center items-center overflow-hidden"
      >
        <div
          class="h-full bg-rose-600 rounded-full transition-all duration-300"
          :class="activeArray[reindex(i - 1)]
            ? 'w-2 md:w-4 lg:w-6 opacity-100'
            : 'w-1 opacity-25'"
        />
      </div>

      <div
        v-for="i in numLasers"
        :key="i"
        class="pt-2 flex justify-center items-center"
      >
        {{ MAJOR_SCALE_NOTES[(i - 1) % 7] }}
      </div>
    </div>
  </div>
</template>
