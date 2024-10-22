<script setup>
import { RouterView } from "vue-router";
import { inject, onMounted, onBeforeUnmount, computed, ref } from "vue";
import { useLaserharpStore } from "./stores/laserharp";
import NavBar from "./components/NavBar.vue";
import NavItemCollection from "./components/NavItemCollection.vue";
import FooterBar from "./components/FooterBar.vue";
import IconLoader from "./components/IconLoader.vue";

const api = inject("api");

const laserharp = useLaserharpStore();
const connected = computed(() => laserharp.connected);

onMounted(() => {
  // api connects autoomatically
});

onBeforeUnmount(() => {
  api.disconnect();
});

const menuOpen = ref();
</script>

<template>
  <div class="w-full h-full flex flex-col select-none">
    <header class="w-full h-12 z-5 shrink-0 bg-darker shadow-lg">
      <NavBar
        v-model:open="menuOpen"
        class="container mx-auto px-8 h-full"
      />
    </header>

    <main class="w-full h-full overflow-x-hidden overflow-y-auto">
      <div class="w-screen min-w-screen">
        <div class="container mx-auto p-8 space-y-8 min-h-full flex flex-col">
          <RouterView />
        </div>
      </div>
    </main>

    <footer class="w-full h-8 z-5 shrink-0 bg-darker shadow-lg">
      <FooterBar class="container mx-auto px-8 h-full" />
    </footer>

    <div
      v-if="menuOpen"
      class="fixed md:hidden inset-0 z-10 bg-darker bg-opacity-95"
      @click="menuOpen = false"
    >
      <nav class="w-full h-full">
        <NavItemCollection class="w-full h-full flex flex-col items-center justify-center space-y-8" />
      </nav>
    </div>

    <div
      v-if="!connected"
      class="fixed inset-0 z-10 bg-black bg-opacity-75 flex items-center justify-center"
    >
      <IconLoader class="scale-50" />
    </div>
  </div>
</template>
