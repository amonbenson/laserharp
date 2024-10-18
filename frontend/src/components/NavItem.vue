<script setup>
import { RouterLink } from "vue-router";
</script>

<template>
  <RouterLink
    class="h-full flex items-center justify-center text-muted truncate transition-colors duration-200 hover:text-secondary-lighter"
    inactive-class="text-muted"
    active-class="text-secondary-lighter"
  >
    <slot />
  </RouterLink>
</template>
