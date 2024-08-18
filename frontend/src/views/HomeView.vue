<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import axios from "axios";

const CAMERA_WIDTH = 640;
const CAMERA_HEIGHT = 480;

const cameraCanvas = ref(null);
let redrawInterval = null;

function resizeCanvas() {
  const canvas = cameraCanvas.value;
  const parent = canvas.parentElement;
  canvas.width = parent.clientWidth;
  canvas.height = parent.clientHeight;
};

async function redrawCanvas() {
  // skip if the canvas is not mounted
  if (!cameraCanvas.value) {
    return;
  }

  // get a frame from the camera
  const frame = await axios.get("/camera/frame", { responseType: "arraybuffer" });
  if (frame.status !== 200) {
    console.error(`Failed to get camera frame: ${frame.status}`);
    return;
  }

  // validate the length
  if (frame.data.byteLength !== CAMERA_WIDTH * CAMERA_HEIGHT) {
    console.error(`Invalid frame length: ${frame.data.byteLength}, expected ${CAMERA_WIDTH * CAMERA_HEIGHT}`);
    return;
  }

  // draw the frame
  const canvas = cameraCanvas.value;
  const context = canvas.getContext("2d");
  const imageData = context.createImageData(640, 480);
  const data = new Uint8Array(frame.data);
  for (let i = 0; i < data.length; i++) {
    imageData.data[i * 4] = data[i];
    imageData.data[i * 4 + 1] = data[i];
    imageData.data[i * 4 + 2] = data[i];
    imageData.data[i * 4 + 3] = 255;
  }
  context.putImageData(imageData, 0, 0);
}

onMounted(async () => {
  resizeCanvas();
  redrawCanvas();

  window.addEventListener("resize", resizeCanvas);
  redrawInterval = setInterval(redrawCanvas, 1000);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCanvas);
  clearInterval(redrawInterval);
});
</script>

<template>
  <main class="w-full h-full relative">
    <div class="absolute inset-8">
      <canvas ref="cameraCanvas"></canvas>
    </div>
  </main>
</template>
