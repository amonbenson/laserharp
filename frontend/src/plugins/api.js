import axios from "axios";
import { io } from "socket.io-client";
import { useLaserharpStore } from "@/stores/laserharp";
import { watch } from "vue";

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

  async emitWithResponse(endpoint, data) {
    return new Promise((resolve, reject) => {
      this.socket.emit(endpoint, data, (response) => {
        if (!response) {
          reject(new Error("No response from server"));
        } else if (response.error) {
          reject(response.error);
        } else {
          resolve(response);
        }
      });
    });
  }

  _parseSettingType(value, description) {
    switch (description.type) {
      case "int":
        return parseInt(value);
      case "float":
        return parseFloat(value);
      case "bool":
        return Boolean(value);
      case "str":
        return String(value);
      default:
        throw new Error(`Unknown setting type: ${description.type}`);
    }
  }

  _parseSetting(value, description) {
    const v = this._parseSettingType(value, description);

    switch (description.type) {
      case "int":
      case "float":
        if (isNaN(v)) throw new Error("Invalid number");
        if (v < description.range[0]) throw new Error("Value too low");
        if (v > description.range[1]) throw new Error("Value too high");
        return v;
      case "bool":
        return v;
      case "str":
        return v;
      default:
        throw new Error(`Unknown setting type: ${description.type}`);
    }
  }

  async updateSetting(componentKey, settingKey, newValue) {
    const laserharp = useLaserharpStore();
    const description = laserharp[componentKey]?.config?.settings?.[settingKey];
    if (!description) {
      console.error(`Setting ${componentKey}.${settingKey} not found`);
      return;
    }

    try {
      // parse the value (convert to the correct type, apply range limits, etc.)
      const value = this._parseSetting(newValue, description);

      // update the setting locally
      const laserharp = useLaserharpStore();
      laserharp.updateSetting(componentKey, settingKey, value);

      // send the new value to the server
      await this.emitWithResponse("app:setting:update", {
        componentKey,
        settingKey,
        value,
      });
    } catch (error) {
      console.error(`Failed to update setting ${componentKey}.${settingKey}: ${error}`);
    }
  }
}

export default {
  install(app, options) {
    const api = new Api(options?.baseUrl || "http://localhost:5000/api");
    app.config.globalProperties.$api = api;
    app.provide("api", api);
  },
};
