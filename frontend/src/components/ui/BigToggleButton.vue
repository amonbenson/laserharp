<script setup>
const props = defineProps({
  label: { type: String, required: true },
  activeDescription: { type: String, required: true },
  inactiveDescription: { type: String, required: true },
  disabled: { type: Boolean, default: false },
});

const model = defineModel({ type: Boolean });
</script>

<template>
  <button
    class="w-48 h-24 rounded-xl shadow-xl group enabled:hover:bg-primary enabled:hover:shadow-primary/20 transition-all flex flex-col justify-center items-center"
    :class="[
      model ? 'bg-primary shadow-primary/10' : 'bg-darker shadow-darker/20',
      props.disabled ? 'opacity-50 cursor-default' : 'cursor-pointer',
    ]"
    :disabled="props.disabled"
    @click="!props.disabled && (model = !model)"
  >
    <h3>{{ label }}</h3>
    <p
      class="group-enabled:group-hover:text-light transition-colors"
      :class="model ? 'text-light' : 'text-muted'"
    >
      {{ model ? props.activeDescription : props.inactiveDescription }}
    </p>
  </button>
</template>
