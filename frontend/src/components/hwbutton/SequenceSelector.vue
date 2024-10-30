<script setup>
import { computed, watch } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import { snakeCaseToTitleCase } from "@/utils";
import TextField from "@/components/ui/TextField.vue";
import SelectField from "@/components/ui/SelectField.vue";
import SequenceIcon from "./SequenceIcon.vue";

const laserharp = useLaserharpStore();

const actions = computed(() => laserharp?.hwbutton?.config?.available_actions ?? []);
const options = computed(() => Object.fromEntries(actions.value.map((action) => ([action, snakeCaseToTitleCase(action)]))));

const props = defineProps({
  sequence: { type: String, default: "xxx" },
});

const model = defineModel({ type: String, defaultValue: "none" });
</script>

<template>
  <div class="h-8 flex space-x-2">
    <SequenceIcon
      class="shrink-0 h-full"
      :sequence="sequence"
    />
    <!-- <TextField class="w-full rounded-full overflow-hidden px-4" v-model="model" /> -->
    <SelectField
      v-model="model"
      class="w-full h-full rounded-full overflow-hidden px-4"
      :options="options"
    />
  </div>
</template>
