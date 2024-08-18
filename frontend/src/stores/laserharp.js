import { defineStore } from "pinia";

export const useLaserharpStore = defineStore("laserharp", {
  state: () => ({
    config: {},
    calibration: {
      ya: 0,
      yb: 0,
      m: [],
      x0: [],
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
    }
  }
});
