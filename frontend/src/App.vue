<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="w-full h-full flex flex-col select-none">
    <header class="w-full h-12 bg-gray-900 text-white flex justify-start items-center">
      <RouterLink to="/" class="mx-8">
        <h1>
          Laserharp
        </h1>
      </RouterLink>
    </header>

    <RouterView class="grow" />
  </div>
</template>
