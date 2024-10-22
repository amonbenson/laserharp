<script setup>
import { ref, computed } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import NavItem from "./NavItem.vue";
import NavItemCollection from "./NavItemCollection.vue";
import { FiMenu, FiX } from "vue3-icons/fi";

const laserharp = useLaserharpStore();
const status = computed(() => {
  if (laserharp.connected) {
    return laserharp.app?.state?.status ?? "unknown";
  } else {
    return "disconnected";
  }
});

const open = defineModel("open", {
  type: Boolean,
  default: false,
});
</script>

<template>
  <nav class="flex items-center justify-between md:justify-start space-x-8">
    <NavItem
      class="z-20"
      active-class="text-light"
      to="/"
      @click="$emit('update:open', false)"
    >
      <h1 class="inline-block">
        Laserharp
      </h1>&ensp;<span
        class="inline-block size-4 rounded-full"
        :class="status === 'running'
          ? 'bg-success'
          : (status === 'calibrating'
            ? 'bg-warning'
            : 'bg-muted')"
      />
    </NavItem>

    <NavItemCollection class="hidden md:flex items-center justify-center space-x-8" />

    <!-- eslint-disable vue/require-explicit-emits -->
    <button
      class="md:hidden z-20 text-light"
      @click="$emit('update:open', !open)"
    >
      <FiMenu
        v-if="!open"
        size="1.5rem"
      />
      <FiX
        v-else
        size="1.5rem"
      />
    </button>
  </nav>
</template>
