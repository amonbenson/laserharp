<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";
import colors from "tailwindcss/colors";

const CAMERA_WIDTH = 640;
const CAMERA_HEIGHT = 480;

const api = inject("api");
const laserharp = useLaserharpStore();

const canvas = ref(null);
let canvasAnimationFrameHandle = null;

const stream = new Image();
stream.src = `${api.axios.defaults.baseURL}/stream.mjpg`;

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
  context.scale(canvas.value.width / CAMERA_WIDTH, canvas.value.height / CAMERA_HEIGHT);

  // draw the camera stream
  context.drawImage(stream, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT);

  // draw the calibration lines
  const calibration = laserharp.calibrator.calibration;
  const result = laserharp.processor.result;
  const mountDistance = laserharp.config?.camera?.mount_distance;

  if (calibration && result && mountDistance) {
    const n = calibration.m.length;

    context.lineCap = "round";

    for (let i = 0; i < n; i++) {
      const x0 = calibration.x0[i];
      const y0 = 0;
      const x1 = calibration.x0[i] + calibration.m[i] * CAMERA_HEIGHT;
      const y1 = CAMERA_HEIGHT;

      // draw the beam line
      context.strokeStyle = colors.rose[600];
      context.lineWidth = 2;
      context.setLineDash([5, 5]);

      context.beginPath();
      context.moveTo(x0 - 1, y0);
      context.lineTo(x1 - 1, y1);
      context.stroke();

      if (!result.active[i]) {
        // draw a red blob if no intersection was detected
        context.fillStyle = colors.rose[600];
        context.beginPath();
        context.arc(x0, y0, 5, 0, 2 * Math.PI);
        context.fill();
      } else {
        // draw a green blob with the modulation depth at the point of intersection
        const y = calculateScreenY(result.length[i], mountDistance, calibration.ya, calibration.yb);
        const modOffset = result.modulation[i] * 70;

        context.fillStyle = colors.rose[600];
        context.strokeStyle = colors.rose[600];
        context.setLineDash([]);

        context.beginPath();
        context.beginPath();
        context.arc(x0, y + modOffset, 5, 0, 2 * Math.PI);
        context.stroke();

        context.beginPath();
        context.arc(x0, y, 5, 0, 2 * Math.PI);
        context.fill();
      }
    }
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
    <canvas
      ref="canvas"
      class="w-full h-full"
    />
  </div>
</template>
