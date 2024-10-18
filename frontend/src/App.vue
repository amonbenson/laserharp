<script setup>
import { RouterLink, RouterView } from "vue-router";
import { inject, onMounted, onBeforeUnmount, computed, watch } from "vue";
import { storeToRefs } from "pinia";
import { useLaserharpStore } from "./stores/laserharp";
import NavBar from "./components/NavBar.vue";
import FooterBar from "./components/FooterBar.vue";
import IconLoader from "./components/IconLoader.vue";

const DEVELOPMENT = process.env.NODE_ENV === "development";

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
    <header class="w-full h-12 shrink-0 bg-darker text-light">
      <NavBar class="container mx-auto px-8 h-full" />
    </header>

    <main class="w-full h-full overflow-x-hidden overflow-y-auto">
      <div class="w-screen min-w-screen">
        <div class="container mx-auto p-8 space-y-8 min-h-full flex flex-col">
          <RouterView />
        </div>
      </div>
    </main>

    <footer class="w-full h-8 shrink-0 bg-darker text-light">
      <FooterBar class="container mx-auto px-8 h-full" />
    </footer>

    <div
      v-if="status === 'disconnected'"
      class="fixed inset-0 z-10 bg-black bg-opacity-75 flex items-center justify-center"
    >
      <IconLoader class="scale-50" />
    </div>
  </div>
</template>
