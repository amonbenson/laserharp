<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, inject } from "vue";
import { useLaserharpStore } from "@/stores/laserharp";

const CAMERA_WIDTH = 640;
const CAMERA_HEIGHT = 480;

const api = inject("api");
const laserharp = useLaserharpStore();

const cameraImage = document.createElement("canvas");
cameraImage.width = CAMERA_WIDTH;
cameraImage.height = CAMERA_HEIGHT;

const canvas = ref(null);
let canvasAnimationFrameHandle = null;

async function parseCameraImage(framebuffer) {
  // validate the length
  if (framebuffer.byteLength !== CAMERA_WIDTH * CAMERA_HEIGHT) {
    console.error(`Invalid frame length: ${framebuffer.byteLength}, expected ${CAMERA_WIDTH * CAMERA_HEIGHT}`);
    return;
  }

  // set the framebuffer data
  const context = cameraImage.getContext("2d");
  const imageData = context.createImageData(640, 480);
  const data = new Uint8Array(framebuffer);
  for (let i = 0; i < data.length; i++) {
    imageData.data[i * 4] = data[i];
    imageData.data[i * 4 + 1] = data[i];
    imageData.data[i * 4 + 2] = data[i];
    imageData.data[i * 4 + 3] = 255;
  }
  context.putImageData(imageData, 0, 0);
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

  context.scale(canvas.value.width / CAMERA_WIDTH, canvas.value.height / CAMERA_HEIGHT);
  // draw the camera image
  context.drawImage(cameraImage, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT);

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

  api.on("app:frame", (data) => {
    const framebuffer = new Uint8Array(atob(data).split("").map((c) => c.charCodeAt(0)));
    parseCameraImage(framebuffer);
  });

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
