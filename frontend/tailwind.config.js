/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "outline-variant": "#c1c7d1",
        background: "#f7f9fb",
        surface: "#f7f9fb",
        "surface-container": "#eceef0",
        "surface-container-low": "#f2f4f6",
        "surface-container-lowest": "#ffffff",
        "on-surface": "#191c1e",
        "on-surface-variant": "#414750",
        primary: "#004473",
        "primary-container": "#0d5c96",
        secondary: "#006c46",
        "secondary-container": "#6af9b5",
        "on-secondary-container": "#007149",
      },
      fontFamily: {
        "headline-md": ["Manrope", "sans-serif"],
        "headline-xl": ["Manrope", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "label-sm": ["Inter", "sans-serif"],
      },
      fontSize: {
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "headline-xl": ["40px", { lineHeight: "48px", fontWeight: "700" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "label-sm": [
          "14px",
          { lineHeight: "20px", letterSpacing: "0.02em", fontWeight: "500" },
        ],
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
