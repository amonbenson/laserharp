<script setup>
import { computed } from "vue";
import NoteLabel from "./NoteLabel.vue";

const MAJOR_SCALE_NOTES = [0, 2, 4, 5, 7, 9, 11];

const props = defineProps({
  orchestrator: { type: Object, default: null },
});

const rootNote = computed(() => props.orchestrator?.config?.root_note ?? 0);
const globalTranspose = computed(() => props.orchestrator?.settings?.global_transpose ?? 0);
const sectionTranspose = computed(() => props.orchestrator?.settings?.section_transpose ?? 0);

const sections = computed(() => props.orchestrator?.state?.active ?? []);
const pedalPositions = computed(() => Array(7).fill(null).map((_, i) =>
  props.orchestrator?.settings?.[`pedal_position_${i}`] ?? 0));
const mutes = computed(() => Array(7).fill(null).map((_, i) =>
  props.orchestrator?.settings?.[`pedal_mute_${i}`] ?? false));

const numSections = computed(() => sections.value.length);
const numLasers = computed(() => sections.value[0]?.length ?? 0);
</script>

<template>
  <div
    class="min-h-64 w-full lg:w-2/3 aspect-[2/1] grid gap-1"
    :style="{
      gridTemplateRows: `repeat(${numSections}, 1fr) auto`,
      gridTemplateColumns: `repeat(${numLasers}, 1fr)`,
    }"
  >
    <!-- Section active bars -->
    <template
      v-for="section, y in sections.slice().reverse()"
      :key="y"
    >
      <template
        v-for="active, x in section"
        :key="x"
      >
        <div
          class="min-w-8 flex justify-center items-center overflow-hidden transition-all duration-100"
          :class="{
            'opacity-10': mutes[x % 7],
          }"
        >
          <div
            class="h-full rounded-full transition-all duration-100 bg-light"
            :class="{
              'w-1 opacity-25': !active,
              'w-2/3 opacity-100': active,
              'bg-primary': x % 7 == 0,
              'bg-secondary': x % 7 == 3,
            }"
          />
        </div>
      </template>
    </template>

    <!-- Note labels -->
    <!-- eslint-disable vue/no-v-html -->
    <div
      v-for="_, x in numLasers"
      :key="x"
      class="pt-2 flex justify-center items-center"
      :class="{
        'opacity-10': mutes[x % 7],
      }"
    >
      <NoteLabel
        :step="x"
        :alteration="pedalPositions[x % 7]"
      />
    </div>
    <!-- eslint-enable vue/no-v-html -->
  </div>
</template>
