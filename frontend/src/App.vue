<script setup>
import { RouterLink, RouterView } from "vue-router";
import { inject, onMounted, onBeforeUnmount } from "vue";
import { useLaserharpStore } from "./stores/laserharp";

const api = inject("api");

const laserharp = useLaserharpStore();

onMounted(() => {
  // api connects autoomatically
});

onBeforeUnmount(() => {
  api.disconnect();
});
</script>

<template>
  <div class="w-full h-full flex flex-col select-none">
    <header class="w-full h-12 bg-gray-900 text-white flex justify-between items-center">
      <RouterLink to="/" class="mx-8">
        <h1>
          Laserharp&nbsp;<span class="inline-block ml-2 size-4 rounded-full bg-gray-500" :class="{
            'bg-rose-600': laserharp.status === 'disconnected',
            'bg-green-500': laserharp.status === 'running',
          }"></span>
        </h1>
      </RouterLink>
    </header>

    <RouterView class="grow" />
  </div>
</template>
