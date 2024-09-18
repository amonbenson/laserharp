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
    <header class="w-full h-12 shrink-0 bg-gray-900 text-white">
      <div class="container mx-auto px-8 h-full flex items-center space-x-8">
        <RouterLink
          to="/"
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
        >
          Calibrate
        </RouterLink>

        <RouterLink
          to="/debug"
        >
          Debug
        </RouterLink>
      </div>
    </header>

    <main class="w-full h-full overflow-y-auto">
      <div class="container mx-auto p-8 space-y-8 min-h-full flex flex-col">
        <RouterView />
      </div>
    </main>
  </div>
</template>
