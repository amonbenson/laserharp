<script setup>
import { RouterLink, RouterView } from "vue-router";
import { inject, onMounted, onBeforeUnmount, computed, watch } from "vue";
import { storeToRefs } from "pinia";
import { useLaserharpStore } from "./stores/laserharp";

const api = inject("api");

const laserharp = useLaserharpStore();

const status = computed(() => {
  if (laserharp.connected) {
    return laserharp.app?.state?.status ?? "unknown";
  } else {
    return "disconnected";
  }
});

onMounted(() => {
  // api connects autoomatically
});

onBeforeUnmount(() => {
  api.disconnect();
});
</script>

<template>
  <div class="w-full h-full flex flex-col select-none">
    <header class="w-full h-12 bg-gray-900 text-white flex items-center">
      <RouterLink
        to="/"
        class="mx-8"
      >
        <h1>
          Laserharp&nbsp;<span
            class="inline-block ml-2 size-4 rounded-full"
            :class="status === 'running'
              ? 'bg-green-500'
              : (status === 'calibrating'
                ? 'bg-yellow-500'
                : 'bg-gray-500')"
          />
        </h1>
      </RouterLink>

      <RouterLink
        to="/calibrate"
        class="mx-8"
      >
        <h2>Calibrate</h2>
      </RouterLink>
    </header>

    <RouterView class="grow" />
  </div>
</template>
