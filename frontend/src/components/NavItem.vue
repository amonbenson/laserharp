<script setup>
import { RouterLink } from "vue-router";
</script>

<template>
  <RouterLink
    v-slot="{ isActive }"
    class="flex items-center justify-center truncate transition-colors duration-200 hover:text-light"
    active-class="text-light"
  >
    <slot />
  </RouterLink>
</template>
