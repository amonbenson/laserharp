import colors from "tailwindcss/colors";

export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      black: colors.black,
      white: colors.white,
      dark: colors.gray[800],
      darker: colors.gray[900],
      light: colors.white,
      muted: colors.gray[500],
      primary: colors.rose[600],
      "primary-lighter": colors.rose[500],
      secondary: colors.sky[500],
      "secondary-lighter": colors.sky[400],
      success: colors.green[500],
      warning: colors.yellow[500],
      danger: colors.rose[600],
    },
    extend: {},
  },
  plugins: [],
};
