import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import vueTsEslintConfig from "@vue/eslint-config-typescript";
import eslintConfigPrettier from "eslint-config-prettier";

export default [
  { ignores: ["dist/**"] },
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  ...vueTsEslintConfig(),
  eslintConfigPrettier,
];
