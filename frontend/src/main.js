import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import api from "./plugins/api";

const DEFAULT_API_PATH = "/api";
const DEFAULT_WS_PATH = "/ws";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(api, {
    baseUrl: import.meta.env.VITE_API_PATH ?? DEFAULT_API_PATH,
    ws: {
        // host: import.meta.env.VITE_WS_HOST ?? DEFAULT_WS_HOST,
        path: import.meta.env.VITE_WS_PATH ?? DEFAULT_WS_PATH,
    },
});

app.mount("#app");
