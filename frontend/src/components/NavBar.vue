<script setup>
import NavItem from "./NavItem.vue";
</script>

<template>
  <div class="flex items-center space-x-8">
    <NavItem to="/">
      <h1 class="text-light">
        Laserharp&nbsp;<span
          class="inline-block ml-2 size-4 rounded-full"
          :class="status === 'running'
            ? 'bg-success'
            : (status === 'calibrating'
              ? 'bg-warning'
              : 'bg-muted')"
        />
      </h1>
    </NavItem>

    <NavItem to="/calibrate">
      Calibrate
    </NavItem>

    <NavItem to="/settings">
      Settings
    </NavItem>

    <NavItem
      v-if="DEVELOPMENT"
      to="/debug"
    >
      Debug
    </NavItem>
  </div>
</template>
