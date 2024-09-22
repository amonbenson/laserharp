import axios from "axios";
import { io } from "socket.io-client";
import { useLaserharpStore } from "@/stores/laserharp";

export class Api {
  constructor(baseUrl) {
    // create axios and socket.io instances
    this.axios = axios.create({
      baseURL: baseUrl,
    });
    this.socket = io("http://localhost:5000", {
      path: "/ws",
      transports: ["websocket"],
    });

    this._setupStore();
  }

  _setupStore() {
    // handle store change callbacks
    const laserharp = useLaserharpStore();

    this.socket.on("connect", () => {
      laserharp.connect();
    });

    this.socket.on("disconnect", () => {
      laserharp.disconnect();
    });

    this.socket.on("app:global_state:init", state => {
      laserharp.globalStateInit(state);
    });

    this.socket.on("app:global_state:change", change => {
      laserharp.globalStateChange(change);
    });

    this.socket.on("app:global_state:changes", changes => {
      changes.forEach(change => {
        laserharp.globalStateChange(change);
      });
    });
  }

  disconnect() {
    this.socket.disconnect();
  }

  async get(endpoint, config) {
    const result = await this.axios.get(endpoint, config);
    if (result.status !== 200) {
      throw new Error(`Failed to GET ${endpoint}: ${result.status}`);
    }

    return result.data;
  }

  on(endpoint, callback) {
    this.socket.on(endpoint, callback);
  }

  off(endpoint, callback) {
    this.socket.off(endpoint, callback);
  }

  once(endpoint, callback) {
    this.socket.once(endpoint, callback);
  }

  emit(endpoint, data) {
    this.socket.emit(endpoint, data);
  }
}

export default {
  install(app, options) {
    const api = new Api(options?.baseUrl || "http://localhost:5000/api");
    app.config.globalProperties.$api = api;
    app.provide("api", api);
  },
};
