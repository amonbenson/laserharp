import pluginVue from "eslint-plugin-vue";

export default [
  {
    ignores: ["*.d.ts", "**/coverage", "**/dist"],
  },
  ...pluginVue.configs["flat/recommended"],
  {
    rules: {
      "indent": ["error", 2, { "SwitchCase": 1 }],
      "quotes": ["error", "double"],
      "semi": ["error", "always"],
      "comma-dangle": ["error", "always-multiline"],
      "no-console": "warn",
      "no-unused-vars": "error",
    },
    languageOptions: {
      sourceType: "module",
    },
  },
];
