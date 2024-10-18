<script setup>
</script>

<template>
  <RouterLink
    class="text-muted truncate transition-colors duration-200 hover:text-secondary-lighter"
    inactive-class="text-muted"
    active-class="text-secondary-lighter"
  >
    <slot />
  </RouterLink>
</template>
