import { defineConfig } from "vite";
import { Schema, ValidateEnv } from "@julr/vite-plugin-validate-env";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    ValidateEnv({
      VITE_API_ENDPOINT: Schema.string({ format: "url", protocol: false, tld: false }),
    }),
    vue(),
    tailwindcss(),
  ],
});
