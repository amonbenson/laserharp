<template>
  <svg
    class="loader"
    width="128"
    height="128"
    viewBox="0 0 128 128"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      class="beam-0"
      d="M64 114L64 14"
      stroke="#E11D48"
      stroke-width="16"
      stroke-linecap="round"
    />
    <path
      class="beam-1"
      d="M64 114L14 27"
      stroke="#E11D48"
      stroke-width="16"
      stroke-linecap="round"
    />
    <path
      class="beam-2"
      d="M64 114L114 27"
      stroke="#E11D48"
      stroke-width="16"
      stroke-linecap="round"
    />
    <path
      class="base"
      d="M39 114H89"
      stroke="white"
      stroke-width="16"
      stroke-linecap="round"
    />
  </svg>
</template>

<style scoped>
.loader > .beam-0 {
  stroke-dasharray: 100;
  animation: dash 600ms infinite ease-in-out alternate;
}

.loader > .beam-1 {
  stroke-dasharray: 100;
  animation: dash 600ms infinite ease-in-out alternate;
  animation-delay: -400ms;
}

.loader > .beam-2 {
  stroke-dasharray: 100;
  animation: dash 600ms infinite ease-in-out alternate;
  animation-delay: -800ms;
}

@keyframes dash {
  to {
    stroke-dashoffset: 30;
  }
}
</style>
