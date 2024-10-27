import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import api from "./plugins/api";

const DEFAULT_API_URL = process.env.NODE_ENV === "production" ? "/api" : "http://:5000/api";
const DEFAULT_WS_HOST = process.env.NODE_ENV === "production" ? "http://" : "http://:5000";
const DEFAULT_WS_PATH = "/ws";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(api, {
    baseUrl: import.meta.env.VITE_API_URL ?? DEFAULT_API_URL,
    ws: {
        host: import.meta.env.VITE_WS_HOST ?? DEFAULT_WS_HOST,
        path: import.meta.env.VITE_WS_PATH ?? DEFAULT_WS_PATH,
    },
});

app.mount("#app");
