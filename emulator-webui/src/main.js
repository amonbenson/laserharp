import { createApp } from "vue";
import { createPahoMqttPlugin } from "vue-paho-mqtt";
import "./style.css";
import App from "./App.vue";

const app = createApp(App);
app.use(createPahoMqttPlugin({
  PluginOptions: {
    autoConnect: true,
    showNotifications: false,
  },
  MqttOptions: {
    host: import.meta.env.VITE_MQTT_HOST,
    port: import.meta.env.VITE_MQTT_PORT,
    clientId: `emulator-webui-${Math.random().toString(16).substring(2, 8)}`,
  },
}));
app.mount("#app");
