import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import api from "./plugins/api";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(api, { baseUrl: import.meta.env.VITE_API_URL || "http://localhost:5000/api" });

app.mount("#app");
