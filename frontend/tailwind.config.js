/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#09090b",
          card: "#121215",
          border: "#27272a",
          hover: "#1c1c21",
          muted: "#71717a"
        },
        brand: {
          red: "#ef4444",
          redDark: "#b91c1c",
          redLight: "#f87171",
          crimson: "#dc2626"
        }
      }
    },
  },
  plugins: [],
}
