<script setup>
import { computed, ref, inject, watch } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import BigToggleButton from "@/components/ui/BigToggleButton.vue";
import NoteLabel from "@/components/NoteLabel.vue";
import PedalSetting from "@/components/PedalSetting.vue";
import SelectField from "@/components/ui/SelectField.vue";
import SequenceSelector from "@/components/hwbutton/SequenceSelector.vue";
import CenterContainer from "@/components/CenterContainer.vue";
import StringSection from "@/components/StringSection.vue";

const PEDAL_ORDER = [1, 0, 6, -1, 2, 3, 4, 5];

const api = inject("api");
const laserharp = useLaserharpStore();

const midiConverterSettings = computed(() => laserharp.orchestrator?.settings);
const pedalPositions = computed(() => Array(7).fill(null)
  .map((_, step) => midiConverterSettings.value?.[`pedal_position_${step}`] ?? 0));
const mutes = computed(() => Array(7).fill(null)
  .map((_, step) => midiConverterSettings.value?.[`pedal_mute_${step}`] ?? false));

const hwbuttonActions = computed(() => Object.fromEntries(Object
  .entries(laserharp?.hwbutton?.settings ?? {})
  .slice(0, 4) // only show the first 4 assignment options
  .filter(([key]) => key.startsWith("sequence_"))
  .map(([key, value]) => ([key.replace("sequence_", ""), value]))));

const MAJOR_SCALE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];
const _pedalPositionsLabel = (positions) => positions
  .map((p, i) => p !== null ? `${MAJOR_SCALE_NOTES[i]}${p > 0 ? "#" : p < 0 ? "b" : ""}` : null)
  .filter((p) => p !== null)
  .join(", ");

const scaleOptions = computed(() => ({
    "Custom": "Custom",
    ...Object.fromEntries((laserharp?.orchestrator?.state?.scale_pedal_positions ?? [])
      .map(({ name, pedal_positions }) => [name, `${name} (${_pedalPositionsLabel(pedal_positions)})`])),
  }));
</script>

<template>
  <center-container title="Quick Actions">
    <div class="flex space-x-4 mb-8">
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
  </center-container>

  <center-container title="Strings">
    <string-section
      :orchestrator="laserharp.orchestrator"
    />
  </center-container>

  <center-container title="Pedals">
    <div class="flex space-x-8">
      <template
        v-for="step, i in PEDAL_ORDER"
        :key="i"
      >
        <PedalSetting
          v-if="step != -1"
          :step="step"
          :position="pedalPositions[step]"
          :mute="mutes[step]"
          @update:position="api.updateSetting('orchestrator', `pedal_position_${step}`, $event)"
          @update:mute="api.updateSetting('orchestrator', `pedal_mute_${step}`, $event)"
        />
        <div
          v-else
          class="w-8 h-1"
        />
      </template>
    </div>
  </center-container>

  <center-container title="Scales">
    <SelectField
      class="w-96"
      :options="scaleOptions"
      :model-value="laserharp.orchestrator?.settings?.selected_scale"
      @update:model-value="api.updateSetting('orchestrator', 'selected_scale', $event)"
    />
  </center-container>

  <center-container title="Buttons">
    <div class="w-full sm:w-96 flex flex-col space-y-2">
      <SequenceSelector
        v-for="value, key in hwbuttonActions"
        :key="key"
        :sequence="key"
        :model-value="value"
        @update:model-value="api.updateSetting('hwbutton', `sequence_${key}`, $event)"
      />
    </div>
  </center-container>
</template>
