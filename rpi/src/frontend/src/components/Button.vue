<script>
export default {
  name: "Button"
}
</script>

<template>
  <button class="bg-rose-600 hover:bg-rose-700 text-white py-1 px-4 rounded">
    <slot></slot>
  </button>
</template>
