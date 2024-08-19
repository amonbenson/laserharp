<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const CAMERA_WIDTH = 640;
const CAMERA_HEIGHT = 480;

const api = inject("api");
const laserharp = useLaserharpStore();

const canvas = ref(null);
let canvasAnimationFrameHandle = null;

const stream = new Image();
stream.src = `${api.axios.defaults.baseURL}/stream.mjpg`;

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
  const calibration = laserharp.calibration;
  if (calibration.m && calibration.x0) {
    const n = calibration.m.length;

    context.strokeStyle = "red";
    context.lineWidth = 2;

    for (let i = 0; i < n; i++) {
      const x0 = calibration.x0[i];
      const y0 = 0;
      const x1 = calibration.x0[i] + calibration.m[i] * CAMERA_HEIGHT;
      const y1 = CAMERA_HEIGHT;

      context.beginPath();
      context.moveTo(x0, y0);
      context.lineTo(x1, y1);
      context.stroke();
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
    <canvas ref="canvas" class="w-full h-full" />
  </div>
</template>
