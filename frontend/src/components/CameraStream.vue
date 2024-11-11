<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import colors from "tailwindcss/colors";

const CAMERA_WIDTH = 640;
const CAMERA_HEIGHT = 480;

const api = inject("api");
const laserharp = useLaserharpStore();

const calibration = computed(() => laserharp.image_calibrator?.state?.calibration);
const result = computed(() => laserharp.image_processor?.state?.result);
const mountDistance = computed(() => laserharp.camera?.config?.mount_distance);

const length_min = computed(() => laserharp.image_processor?.config?.length_min);
const length_max = computed(() => laserharp.image_processor?.config?.length_max);

const sectionStarts = computed(() => laserharp.orchestrator?.settings
  ? [
    laserharp.orchestrator.settings.section_start_0,
    laserharp.orchestrator.settings.section_start_1,
    laserharp.orchestrator.settings.section_start_2,
  ]
  : null);


const canvas = ref(null);
let canvasAnimationFrameHandle = null;

// const stream = new Image();
// stream.src = `${api.axios.defaults.baseURL}/stream.mjpg`;
const stream = ref(null);

function calculateScreenY(yMetric, mountDistance, ya, yb) {
  const yTan = yMetric / mountDistance;
  const yAngle = Math.atan(yTan);
  const yScreen = yAngle * (yb - ya) / (Math.PI / 2) + ya;
  return yScreen;
}

function onResize() {
  // resize the drawing canvas
  const parent = canvas.value.parentElement;
  canvas.value.width = parent.clientWidth;
  canvas.value.height = parent.clientWidth * (CAMERA_HEIGHT / CAMERA_WIDTH);
};

function onRedraw() {
  const context = canvas.value.getContext("2d");

  // reset transform
  context.setTransform(1, 0, 0, 1, 0, 0);

  // clear the canvas
  context.clearRect(0, 0, canvas.value.width, canvas.value.height);

  // scale the drawing to fit the camera resolution
  context.scale(canvas.value.width / CAMERA_WIDTH, -canvas.value.height / CAMERA_HEIGHT);
  context.translate(0, -CAMERA_HEIGHT);

  try {
    // draw the camera stream (not required anymore, stream is now in a separate <img> element)
    // context.drawImage(stream.value, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT);
  } catch (error) {
    // draw a black rectangle if the stream is not available
    context.fillStyle = "black";
    context.fillRect(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT);
  }

  // draw the calibration lines
  if (calibration.value && result.value && mountDistance.value && sectionStarts.value) {
    const n = calibration.value.m.length;

    context.lineCap = "round";

    for (let i = 0; i < n; i++) {
      const x0 = calibration.value.x0[i];
      const y0 = 0;
      const x1 = calibration.value.x0[i] + calibration.value.m[i] * CAMERA_HEIGHT;
      const y1 = CAMERA_HEIGHT;

      // draw the beam line
      context.strokeStyle = colors.rose[600];
      context.lineWidth = 2;
      context.setLineDash([5, 5]);

      context.beginPath();
      context.moveTo(x0, y0);
      context.lineTo(x1, y1);
      context.stroke();

      // draw a blob at the point of intersection
      if (result.value.active[i]) {
        const y = calculateScreenY(result.value.length[i], mountDistance.value, calibration.value.ya, calibration.value.yb);
        const x = x0 + y * calibration.value.m[i];

        const yMod = y + result.value.modulation[i] * 70;
        const xMod = x0 + yMod * calibration.value.m[i];

        context.fillStyle = colors.rose[600];
        context.strokeStyle = colors.rose[600];
        context.setLineDash([]);

        context.beginPath();
        context.beginPath();
        context.arc(xMod, yMod, 5, 0, 2 * Math.PI);
        context.stroke();

        context.beginPath();
        context.arc(x, y, 5, 0, 2 * Math.PI);
        context.fill();
      }
    }

    // draw the section lines
    context.strokeStyle = colors.sky[500];
    context.lineWidth = 2;
    context.setLineDash([5, 5]);

    for (let i = 0; i < sectionStarts.value.length; i++) {
      const y = calculateScreenY(sectionStarts.value[i], mountDistance.value, calibration.value.ya, calibration.value.yb);

      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(CAMERA_WIDTH, y);
      context.stroke();
    }

    // draw the length limits
    context.strokeStyle = colors.white;
    const yMin = calculateScreenY(length_min.value, mountDistance.value, calibration.value.ya, calibration.value.yb);
    context.beginPath();
    context.moveTo(0, yMin);
    context.lineTo(CAMERA_WIDTH, yMin);
    context.stroke();

    const yMax = calculateScreenY(length_max.value, mountDistance.value, calibration.value.ya, calibration.value.yb);
    context.beginPath();
    context.moveTo(0, yMax);
    context.lineTo(CAMERA_WIDTH, yMax);
    context.stroke();
  }
}

onMounted(() => {
  onResize();
  window.addEventListener("resize", onResize);

  const continuousRedraw = () => {
    onRedraw();
    canvasAnimationFrameHandle = requestAnimationFrame(continuousRedraw);
  };
  continuousRedraw();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  cancelAnimationFrame(canvasAnimationFrameHandle);
});
</script>

<template>
  <div class="aspect-[4/3]">
    <div class="relative w-full h-full">
      <img
        ref="stream"
        class="absolute left-0 top-0 w-full h-full -scale-y-100"
        :src="`${api.axios.defaults.baseURL}/stream.mjpg`"
      >
      <canvas
        ref="canvas"
        class="absolute left-0 top-0 w-full h-full"
      />
    </div>
  </div>
</template>
