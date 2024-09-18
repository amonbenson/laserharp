import { defineStore } from "pinia";

const traversePath = (obj, path) => {
  return path.reduce((acc, key) => acc[key], obj);
};

export const useLaserharpStore = defineStore("laserharp", {
  state: () => ({
    app: {
      status: "disconnected",
    },
    connected: false,
  }),
  actions: {
    connect() {
      this.connected = true;
    },
    disconnect() {
      this.connected = false;
    },
    globalStateInit(state) {
      for (const key in state) {
        this[key] = state[key];
      }
    },
    globalStateChange({ change_type, path, ...args }) {
      // remove the "root" key
      if (path[0] === "root") {
        path = path.slice(1);
      }

      // if we have an update change, we need to find the parent object
      let updateKey = null;
      if (change_type === "update") {
        updateKey = path.pop();
      }

      // traverse the path along the global st
      let node = null;
      try {
        node = traversePath(this, path);
      } catch (e) {
        console.error(`Failed to apply change to ${path.join(".")}:`, e);
        return;
      }

      // apply the change
      switch (change_type) {
        case "add":
          switch (args.repr) {
            case "atomic":
              node[args.key] = args.value;
              break;
            case "list":
              node[args.key] = [];
              break;
            case "dict":
              node[args.key] = {};
              break;
            default:
              console.error("Unknown repr", args.repr);
              break;
          }
          break;
        case "remove":
          delete node[args.key];
          break;
        case "update":
          node[updateKey] = args.value;
          break;
        default:
          console.error("Unknown change type", change_type);
          break;
      }
    },
  },
});

export const useGlobalState = () => useLaserharpStore().globalState;
