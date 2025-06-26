<script setup>
import NavItem from "./NavItem.vue";

const DEVELOPMENT = process.env.NODE_ENV === "development";
</script>

<template>
  <div>
    <NavItem to="/camera">
      Camera
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
