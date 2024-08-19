import { defineStore } from "pinia";

export const useLaserharpStore = defineStore("laserharp", {
  state: () => ({
    config: {},
    calibrator: {
      calibration: null,
    },
    processor: {
      result: null,
    },
    status: "connecting",
    connected: false,
  }),
  actions: {
    connect() {
      this.connected = true;
      this.status = "connected";
    },
    disconnect() {
      this.connected = false;
      this.status = "disconnected";
    },
  },
});
