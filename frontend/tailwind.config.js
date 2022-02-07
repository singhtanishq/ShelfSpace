/** @type {import('tailwindcss').Config} */
import defaultTheme from "tailwindcss/defaultTheme";
import colors from "tailwindcss/colors";
import flattenColorPalette from "tailwindcss/lib/util/flattenColorPalette";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4fb",
          100: "#d9e6f5",
          200: "#b3cde9",
          300: "#84add9",
          400: "#5489c4",
          500: "#356cab",
          600: "#27578c",
          700: "#1e3a5f",
          800: "#182f4c",
          900: "#13253d",
          950: "#0c1828",
        },
        accent: colors.amber,
      },
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
        serif: ["Georgia", "Cambria", "serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(19 37 61 / 0.08), 0 1px 2px -1px rgb(19 37 61 / 0.08)",
        "card-hover": "0 10px 24px -6px rgb(19 37 61 / 0.18)",
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.3s ease-out both",
      },
    },
  },
  plugins: [withVariables],
};

// exposed CSS variables (used for theming inputs consistently)
function withVariables({ addBase, theme }: any) {
  addBase({
    ":root": {
      ...Object.fromEntries(
        Object.entries(flattenColorPalette(theme("colors"))).map(([k, v]) => [`--color-${k}`, v])
      ),
    },
  });
}
